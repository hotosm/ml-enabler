import tensorflow as tf
import os

flags = tf.compat.v1.flags
FLAGS = flags.FLAGS

def _augment_helper(image):
    """Augment an image with flipping/brightness changes"""
    image = tf.image.random_flip_left_right(image)
    image= tf.image.rot90(image, tf.random.uniform(shape=[], minval=0, maxval=4, dtype=tf.int32))
    return image


def _parse_helper(example, n_chan, n_classes, shp=[256, 256, 3]):
    """"Parse TFExample record containing image and label."""""

    example_fmt = {"image": tf.io.FixedLenFeature([], tf.string),
                   "label": tf.io.FixedLenFeature([], tf.string)}
    parsed = tf.io.parse_single_example(example, example_fmt)

    # Get label, decode
    label = tf.io.parse_tensor(parsed['label'], tf.uint8)
    label = tf.reshape(label, [-1])

    # Get image string, decode
    image = tf.image.decode_image(parsed['image'])
    image = tf.reshape(image, shp)

    # convert image from RGB to grayscale to reduce the feature complexity
    image = tf.image.rgb_to_grayscale(image)
    
    # restore to 3 channel dimensions as required by the net 
    # by stacking the grayscale channel x3
    image = tf.image.grayscale_to_rgb(image)

    # change dtype to float32
    image = tf.cast(image, tf.float32)

    # re-scale pixel values between 0 and 1
    image = tf.divide(image, 255)

    return image, label


def parse_and_augment_fn(example, n_chan=3, n_classes=11, shp=[256, 256, 3]):
    """Parse TFExample record containing image and label and then augment image."""
    image, label = _parse_helper(example, n_chan, n_classes, shp)
    image = _augment_helper(image)
    return image, label


def parse_fn(example, n_chan=3, n_classes=11, shp=[256,256,3]):
    """Parse TFExample record containing image and label."""
    image, label = _parse_helper(example, n_chan, n_classes, shp)
    return image, label


def make_dataset(path):
    dataset = tf.data.TFRecordDataset(path)
    dataset = dataset.shuffle(buffer_size=FLAGS.shuffle_buffer_size)
    dataset = dataset.map(map_func=parse_fn, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    dataset = dataset.batch(batch_size=FLAGS.batch_size)
    dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
    return dataset

def _parse_image_function(example_proto):
    image_feature_description = {
        'image': tf.io.FixedLenFeature([], tf.string),
        'label': tf.io.FixedLenFeature([], tf.string)
    }
    return tf.io.parse_single_example(example_proto, image_feature_description)


def get_example(tfrecords_path):
    dataset = tf.data.TFRecordDataset([tfrecords_path])

    parsed_image_dataset = dataset.map(_parse_image_function)

    for image_features in parsed_image_dataset:
        image_raw = image_features['image'].numpy()
        img = tf.image.decode_image(image_raw)

        label = image_features['label'].numpy()
        label = tf.io.parse_tensor(label.numpy(), tf.uint8).numpy()
    return img, label


def get_dataset_feeder(fpath, data_map_func=None, shuffle_buffer_size=None,
                       repeat=True, n_map_threads=4, batch_size=16,
                       cycle_length=1, prefetch_buffer_size=None):
    """Returns a TF Dataset for training/evaluating TF Estimators"""

    files = tf.io.matching_files(os.path.join(fpath))
    shards = tf.data.Dataset.from_tensor_slices(files)
    shards = shards.shuffle(buffer_size=4)

    ds = tf.data.TFRecordDataset(shards)

    #TODO: use `shuffle_and_repeat` in v1.13+
    #ds = ds.shuffle_and_repeat(buffer_size=shuffle_buffer_size)
    if shuffle_buffer_size:
        ds = ds.shuffle(shuffle_buffer_size)
    if repeat:
        ds = ds.repeat()
    if data_map_func:
        ds = ds.map(map_func=data_map_func, num_parallel_calls=n_map_threads)
    ds = ds.batch(batch_size=batch_size)
    if prefetch_buffer_size:
        ds = ds.prefetch(buffer_size=prefetch_buffer_size)

    return ds