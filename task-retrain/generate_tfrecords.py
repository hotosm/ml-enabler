import tensorflow as tf
import shutil
import numpy as np

def _bytes_feature(value):
    """Returns a bytes_list from a single image numpy array representation from label maker ie npz['x_train'][i]"""
    img = tf.convert_to_tensor(value)
    img_t_encode = tf.image.encode_png(img, compression=-1)

    if isinstance(img_t_encode, type(tf.constant(0))):
        value_b = img_t_encode.numpy()  # BytesList won't unpack a string from an EagerTensor
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value_b]))


def _bytes_feature_label(value):
    """Returns a bytes_list from a single label numpy array representation from label maker ie npz['y_train'][i]"""
    label = tf.convert_to_tensor(value)
    label = tf.io.serialize_tensor(label)

    if isinstance(label, type(tf.constant(0))):
        label_b = label.numpy()  # BytesList won't unpack a string from an EagerTensor
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[label_b]))


def gen_tf_image_example(img, label):
    feature = {
        'image': _bytes_feature(img),
        'label': _bytes_feature_label(label)}
    return tf.train.Example(features=tf.train.Features(feature=feature))


def create_tfr(npz_path, city, dest_folder='/tmp/tfrecords/', n_imgs_shard=800):
    """
    Converts a data.npz file with keys train, test, and val into a 3 tf records files (train, test, and val).
   """
    npz = np.load(npz_path)
    train_shp = npz['y_train'].shape[0]

    if train_shp > n_imgs_shard:
        train_shards_num = round(train_shp / n_imgs_shard)
        train_split_x = np.array_split(npz['x_train'], train_shards_num)
        train_split_y = np.array_split(npz['y_train'], train_shards_num)

        for i in np.arange(0, train_shards_num):
            path = dest_folder + 'train_{}_{}.tfrecords'.format(city, i)
            with tf.io.TFRecordWriter(path) as writer:
                z = zip(train_split_x[i], train_split_y[i])
                for img, label in z:
                    tf_example = gen_tf_image_example(img, label)
                    writer.write(tf_example.SerializeToString())
        print('TFrecords created for train.')
    else:
        print(dest_folder)
        path = dest_folder + 'train_{}.tfrecords'.format(city)
        print(path)
        with tf.io.TFRecordWriter(path) as writer:
            z = zip(npz['x_train'], npz['y_train'])
            for img, label in z:
                tf_example = gen_tf_image_example(img, label)
                writer.write(tf_example.SerializeToString())
            print('TFrecords created for train.')

    test_shp = npz['y_test'].shape[0]
    if test_shp > n_imgs_shard:
        test_shards_num = round(test_shp / n_imgs_shard)
        test_split_x = np.array_split(npz['x_test'], test_shards_num)
        test_split_y = np.array_split(npz['y_test'], test_shards_num)

        for i in np.arange(0, test_shards_num):
            path = dest_folder + 'test_{}_{}.tfrecords'.format(city, i)
            print(path)
            with tf.io.TFRecordWriter(path) as writer:
                z = zip(test_split_x[i], test_split_y[i])
                for img, label in z:
                    tf_example = gen_tf_image_example(img, label)
                    writer.write(tf_example.SerializeToString())
        print('TFrecords created for test.')

    else:
        path = dest_folder + 'test_{}.tfrecords'.format(city)
        with tf.io.TFRecordWriter(path) as writer:
            z = zip(npz['x_test'], npz['y_test'])
            for img, label in z:
                tf_example = gen_tf_image_example(img, label)
                writer.write(tf_example.SerializeToString())
            print('TFrecords created for test.')

    val_shp = npz['y_val'].shape[0]
    if val_shp > n_imgs_shard:
        val_shards_num = round(val_shp / n_imgs_shard)
        val_split_x = np.array_split(npz['x_val'], val_shards_num)
        val_split_y = np.array_split(npz['y_val'], val_shards_num)

        for i in np.arange(0, val_shards_num):
            path = dest_folder + 'val_{}_{}.tfrecords'.format(city, i)
            with tf.io.TFRecordWriter(path) as writer:
                z = zip(val_split_x[i], val_split_y[i])
                for img, label in z:
                    tf_example = gen_tf_image_example(img, label)
                    writer.write(tf_example.SerializeToString())
        print('TFrecords created for val.')
    else:
        path = dest_folder + 'val_{}.tfrecords'.format(city)
        with tf.io.TFRecordWriter(path) as writer:
            z = zip(npz['x_val'], npz['y_val'])
            for img, label in z:
                tf_example = gen_tf_image_example(img, label)
                writer.write(tf_example.SerializeToString())
        print('TFrecords created for val.')

    #zip up tf-records 
    shutil.make_archive(dest_folder, 'zip', dest_folder)