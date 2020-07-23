"""
Script specifying TF estimator object for training/serving
@author: DevelopmentSeed
"""

import os
import os.path as op
import json
import numpy as np
import pandas as pd
import shutil
import glob

from functools import partial

from absl import app, flags, logging

from tqdm import tqdm

import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.applications import ResNet50, Xception
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.estimator import model_to_estimator
from tensorflow.keras.optimizers import Adam, SGD, RMSprop

from utils_train import FBetaScore
from utils_readtfrecords import parse_and_augment_fn, parse_fn, get_dataset_feeder
from utils_loss import sigmoid_focal_crossentropy

from sklearn.metrics import precision_score, recall_score, fbeta_score

FLAGS = flags.FLAGS

#overwrite these flags when calling model.py 
flags.DEFINE_integer('n_classes', 2, 'Number of classes in dataset')
flags.DEFINE_list('class_names', ['not_industrial', 'industrial'],
                  'class names in data set')
flags.DEFINE_integer('n_train_samps', 400, 'number of samples in training set')
flags.DEFINE_integer('n_val_samps', 100, 'number of samples in validation set')
flags.DEFINE_list('x_feature_shape', [-1, 256, 256, 3], 'x feature shape')
flags.DEFINE_string('x_feature_name', 'input_1', 'layer name')

flags.DEFINE_integer('cycle_length', 1, 'cycle length')
flags.DEFINE_integer('n_map_threads', 4, 'threads')
flags.DEFINE_integer('shuffle_buffer_size', None, 'should match size of train dataset')
flags.DEFINE_integer('prefetch_buffer_size', 1, 'prefetch buffer size')

flags.DEFINE_string('tf_train_data_dir', '/ml/data',
                    'Path to data dir on GCS.')
flags.DEFINE_string('tf_val_data_dir', '/ml/data', 'Path to data dir')
flags.DEFINE_string('tf_test_data_dir', None, 'Path to data dir')

flags.DEFINE_string('tf_model_dir', '/ml/models/', 'Path or GCS directory to save models.')
flags.DEFINE_string('tf_test_results_dir', None, 'Path to GCS to write results')
flags.DEFINE_string('model_id', 'a', 'model id for saving')

flags.DEFINE_string('tf_test_ckpt_path', None, 'Use to override training and run prediction on test data.')

flags.DEFINE_integer('tf_steps_per_summary', 10, 'Training steps per Tensorboard events save.')
flags.DEFINE_integer('tf_steps_per_checkpoint', 100, 'Training steps per model checkpoint save.')
flags.DEFINE_integer('tf_batch_size', 16, 'Size of one batch for training')
flags.DEFINE_integer('tf_train_steps', 200, 'The number of training steps to perform')

flags.DEFINE_integer('tf_dense_size_a', 256, 'Size of final dense hidden layer')
flags.DEFINE_float('tf_dense_dropout_rate_a', 0.3, 'Dropout rate of the final dense hidden layer')
flags.DEFINE_integer('tf_dense_size', 128, 'Size of final dense hidden layer')
flags.DEFINE_float('tf_dense_dropout_rate', 0.35, 'Dropout rate of the final dense hidden layer')
flags.DEFINE_string('tf_dense_activation', 'relu', 'Activation output layer')
flags.DEFINE_float('tf_learning_rate', 0.001, 'learning rate for training')
flags.DEFINE_string('tf_optimizer', 'adam', 'Optimizer function')


######################
# Modeling Code
######################
def resnet50_estimator(params, model_dir, run_config):
    """Get a Resnet50 model as a tf.estimator object"""

    # Get the original resnet model pre-initialized weights
    base_model = Xception(weights='imagenet',
                          include_top=False,  # Peel off top layer
                          pooling='avg',
                          input_shape=params['input_shape'])
    # Get final layer of base Resnet50 model
    x = base_model.output
    # Add a fully-connected layer
    x = Dense(params['dense_size_a'],
              activation=params['dense_activation'],
              name='dense')(x)
    # Add (optional) dropout and output layer
    x = Dropout(rate=params['dense_dropout_rate_a'])(x)
    x = Dense(params['dense_size'],
              activation=params['dense_activation'],
              name='dense_preoutput')(x)
    x = Dropout(rate=params['dense_dropout_rate'])(x)
    output = Dense(params['n_classes'], name='output', activation='sigmoid')(x)

    model = Model(inputs=base_model.input, outputs=output)

    # Get (potentially decaying) learning rate
    optimizer = get_optimizer(params['optimizer'], params['learning_rate'])
    model.compile(optimizer=optimizer,
                  loss=params['loss'], metrics=params['metrics'])

    # Return estimator
    m_e = model_to_estimator(keras_model=model, model_dir=model_dir + FLAGS.model_id,
                             config=run_config)
    return m_e


def get_optimizer(opt_name, lr, momentum=0.9):
    """Helper to get optimizer from text params"""
    if opt_name == 'adam':
        return Adam(learning_rate=lr)
    if opt_name == 'sgd':
        return SGD(learning_rate=lr)
    if opt_name == 'rmsprop':
        return RMSprop(learning_rate=lr, momentum=momentum)
    raise ValueError('`opt_name`: {} not understood.'.format(opt_name))


def resnet_serving_input_receiver_fn():
    """Convert b64 string encoded images into a tensor for production"""
    def decode_and_resize(image_str_tensor):
        """Decodes image string, resizes it and returns a uint8 tensor."""
        image = tf.image.decode_image(image_str_tensor,
                                      channels=3,
                                      dtype=tf.uint8)
        image = tf.reshape(image, FLAGS.x_feature_shape[1:])
        return image

    # Run processing for batch prediction.
    input_ph = tf.compat.v1.placeholder(tf.string, shape=[None], name='image_binary')
    with tf.device("/cpu:0"):
        images_tensor = tf.map_fn(decode_and_resize, input_ph, back_prop=False, dtype=tf.uint8)

    # Cast to float
    images_tensor = tf.cast(images_tensor, dtype=tf.float32)

    # re-scale pixel values between 0 and 1
    images_tensor = tf.divide(images_tensor, 255)

    return tf.estimator.export.ServingInputReceiver(
        {FLAGS.x_feature_name: images_tensor},
        {'image_bytes': input_ph})


def main(_):
    """
    Function to run TF Estimator
    Note: set the `TF_CONFIG` environment variable according to:
    https://www.tensorflow.org/api_docs/python/tf/estimator/train_and_evaluate
    """

    ###################################
    # Set parameters/config
    ###################################

    # Set logging info so it'll be written the command line
    logging.set_verbosity(logging.INFO)

    os.environ['TF_CONFIG'] = '{}'
    os.environ['_TF_CONFIG_ENV'] = '{}'

    # Set a bunch of TF config params
    tf_config = os.environ.get('TF_CONFIG', '{}')
    logging.info("TF_CONFIG %s", tf_config)
    tf_config_json = json.loads(tf_config)
    cluster = tf_config_json.get('cluster')
    job_name = tf_config_json.get('task', {}).get('type')
    task_index = tf_config_json.get('task', {}).get('index')
    logging.info("cluster=%s job_name=%s task_index=%s", cluster, job_name,
                 task_index)

    is_chief = False
    if not job_name or job_name.lower() in ["chief", "master"]:
        is_chief = True
        logging.info("Will export model.")
    else:
        logging.info("Won't export model.")

    print('TF_CONFIG: {}'.format(os.environ['TF_CONFIG']))
    print('_TF_CONFIG_ENV: {}'.format(os.environ['_TF_CONFIG_ENV']))

    run_config = tf.estimator.RunConfig(model_dir=FLAGS.tf_model_dir + FLAGS.model_id,
                                        save_summary_steps=FLAGS.tf_steps_per_summary,
                                        save_checkpoints_steps=FLAGS.tf_steps_per_checkpoint,
                                        log_step_count_steps=FLAGS.tf_steps_per_summary)

    model_params = {"n_classes": FLAGS.n_classes,
                    "input_shape": FLAGS.x_feature_shape[1:4],
                    "train_steps": FLAGS.tf_train_steps,
                    "dense_size_a": FLAGS.tf_dense_size_a,
                    "dense_size": FLAGS.tf_dense_size,
                    "dense_activation": FLAGS.tf_dense_activation,
                    "dense_dropout_rate_a": FLAGS.tf_dense_dropout_rate_a,
                    "dense_dropout_rate": FLAGS.tf_dense_dropout_rate,
                    "optimizer": FLAGS.tf_optimizer,
                    "metrics": [tf.keras.metrics.Precision(), tf.keras.metrics.Recall(),
                                FBetaScore(num_classes=2, beta=2.0, average='weighted')],
                    "learning_rate": FLAGS.tf_learning_rate,
                    #"loss": sigmoid_focal_crossentropy,
                    "loss": tf.keras.losses.BinaryCrossentropy(),
                    "class_names": FLAGS.class_names,
                    "n_train_samps": FLAGS.n_train_samps,
                    "n_val_samps": FLAGS.n_val_samps}

    def precision_m(labels, predictions):
        precision_metric = tf.keras.metrics.Precision(name="precision_m")
        precision_metric.update_state(y_true=labels, y_pred=predictions['output'])
        return {"precision_m": precision_metric}

    def recall_m(labels, predictions):
        recall_metric = tf.keras.metrics.Recall(name="recall_m")
        recall_metric.update_state(y_true=labels, y_pred=predictions['output'])
        return {"recall_m": recall_metric}

    def fbeta_m(labels, predictions):
        fbeta_metric = FBetaScore(num_classes=2, beta=2.0, average='weighted', threshold=.5)
        fbeta_metric.update_state(y_true=labels, y_pred=predictions['output'])
        return {"fbeta_m": fbeta_metric}

    classifier = resnet50_estimator(model_params, FLAGS.tf_model_dir, run_config)
    classifier = tf.estimator.add_metrics(classifier, fbeta_m)
    classifier = tf.estimator.add_metrics(classifier, precision_m)
    classifier = tf.estimator.add_metrics(classifier, recall_m)

    ###################################
    # Check if user wants to run test
    ###################################
    # Create test dataset function if needed
    if FLAGS.tf_test_ckpt_path:
        print('Overriding training and running test set prediction with model ckpt: {}'.format(
            FLAGS.tf_test_ckpt_path))

        if not os.path.exists(FLAGS.tf_test_results_dir):
            os.makedirs(FLAGS.tf_test_results_dir)

        logging.info('Beginning test for model')

        # Create test data function, get `y_true`
        fpath_test = op.join(FLAGS.tf_test_data_dir, 'test.tfrecords')
        map_func = partial(parse_fn, n_chan=3,
                           n_classes=model_params['n_classes'])

        dataset_test = get_dataset_feeder(fpath=fpath_test,
                                          data_map_func=map_func,
                                          shuffle_buffer_size=None,
                                          repeat=False,
                                          n_map_threads=FLAGS.n_map_threads,
                                          batch_size=1,  # Use bs=1 here to count samples instead of batches
                                          cycle_length=FLAGS.cycle_length,
                                          prefetch_buffer_size=FLAGS.prefetch_buffer_size)
        y_true = []
        for features in dataset_test:
            y_true.append(features[1].numpy()[0])
        print('Found {} total samples to test.'.format(len(y_true)))

        # Reset the dataset iteration for prediction
        dataset_test_fn = partial(get_dataset_feeder,
                                  fpath=fpath_test,
                                  data_map_func=map_func,
                                  shuffle_buffer_size=None,
                                  repeat=False,
                                  n_map_threads=FLAGS.n_map_threads,
                                  batch_size=FLAGS.tf_batch_size,
                                  cycle_length=FLAGS.cycle_length,
                                  prefetch_buffer_size=FLAGS.prefetch_buffer_size)

        # Reset test iterator and run predictions
        raw_preds = classifier.predict(dataset_test_fn,
                                       yield_single_examples=True,
                                       checkpoint_path=FLAGS.tf_test_ckpt_path)

        p_list = [raw_pred['output'] for raw_pred in raw_preds]

        preds = []
        for i in tqdm(range(len(p_list)), miniters=1000):
            a = p_list[i] >= 0.5
            a = a.astype(int)
            preds.append(a)

        output_d = {"raw_prediction": p_list,
                    "threshold": preds,
                    "true-label": y_true}

        df_pred = pd.DataFrame.from_dict(output_d)
        df_pred.to_csv(FLAGS.tf_test_results_dir + 'preds.csv') #make into flag

        print('preds csv written')

        recall_lst = []
        for i in np.arange(0, FLAGS.n_classes):
            recall_lst.append(recall_score(np.array(y_true)[:, i], np.array(preds)[:, i]))

        precision_lst = []
        for i in np.arange(0, FLAGS.n_classes):
            precision_lst.append(precision_score(np.array(y_true)[:, i], np.array(preds)[:, i]))

        f_lst = []
        for i in np.arange(0, FLAGS.n_classes):
            f_lst.append(fbeta_score(np.array(y_true)[:, i], np.array(preds)[:, i], beta=2))

        d = {'Precision': precision_lst,
             'Recall': recall_lst,
             'fbeta_2': f_lst,
             'POI': model_params['class_names']}

        df = pd.DataFrame.from_dict(d)
        df['POI'] = model_params['class_names']
        df.to_csv(FLAGS.tf_test_results_dir + 'test_stats.csv') #make into flag

        print("test stats written")
        return d

    ###################################
    # Create data feeder functions
    ###################################

    ## download data from GCS

    #list_and_download_blobs(FLAGS.gcs_bucket_name, FLAGS.local_dataset_dirs)

    # Create training dataset function
    fpath_train = op.join(FLAGS.tf_train_data_dir, 'train_*.tfrecords')
    map_func = partial(parse_and_augment_fn, n_chan=3,
                       n_classes=model_params['n_classes'])

    dataset_train_fn = partial(get_dataset_feeder,
                               fpath=fpath_train,
                               data_map_func=map_func,
                               shuffle_buffer_size=FLAGS.shuffle_buffer_size,
                               repeat=True,
                               n_map_threads=FLAGS.n_map_threads,
                               batch_size=FLAGS.tf_batch_size,
                               cycle_length=FLAGS.cycle_length,
                               prefetch_buffer_size=FLAGS.prefetch_buffer_size)

    # Create validation dataset function
    fpath_validate = op.join(FLAGS.tf_val_data_dir, 'val_*.tfrecords')
    map_func = partial(parse_fn, n_chan=3,
                       n_classes=model_params['n_classes'])

    dataset_validate_fn = partial(get_dataset_feeder,
                                  fpath=fpath_validate,
                                  data_map_func=map_func,
                                  shuffle_buffer_size=FLAGS.shuffle_buffer_size,
                                  repeat=True,
                                  n_map_threads=FLAGS.n_map_threads,
                                  batch_size=FLAGS.tf_batch_size,
                                  cycle_length=FLAGS.cycle_length,
                                  prefetch_buffer_size=FLAGS.prefetch_buffer_size)

    ###################################
    # Run train/val w/ estimator object
    ###################################

    # Set up train and evaluation specifications
    train_spec = tf.estimator.TrainSpec(input_fn=dataset_train_fn,
                                        max_steps=FLAGS.tf_train_steps)

    logging.info("export final pre")
    export_final = tf.estimator.FinalExporter(FLAGS.model_id,
                                              serving_input_receiver_fn=resnet_serving_input_receiver_fn)
    logging.info("export final post")
    #
    eval_spec = tf.estimator.EvalSpec(input_fn=dataset_validate_fn,
                                      steps=FLAGS.n_val_samps,  # Evaluate until complete
                                      exporters=export_final,
                                      throttle_secs=1,
                                      start_delay_secs=1)
    logging.info("eval spec")

    ###################################
    # Run training, save if needed
    ###################################
    logging.info("train and evaluate")
    tf.estimator.train_and_evaluate(classifier, train_spec, eval_spec)
    logging.info("training done.")

    ############################################################################
    # Upload checkpoints, tf events, and model exported for evaluation to AWS
    ############################################################################

    logging.info("zipping model export")
    d = '/ml/models/' + FLAGS.model_id + '/export/' + FLAGS.model_id + '/*'
    dir_name = glob.glob(d)[0]
    logging.info(dir_name)
    shutil.make_archive('/ml/models/model', 'zip', dir_name)
    logging.info('written export as zip file')



#TO-DO


if __name__ == '__main__':
    app.run(main)
