# code adopted from LabelMaker (https://github.com/developmentseed/label-maker)
import os
from os import path as op
import requests 
import rasterio  

from requests.auth import HTTPBasicAuth
from io import BytesIO
from base64 import b64encode
from urllib.parse import urlparse
from typing import Dict, List, NamedTuple, Callable, Optional, Tuple, Any, Iterator
from rasterio.io import MemoryFile
from rasterio.windows import Window
from PIL import Image
import io

import mercantile
from mercantile import Tile, children
import numpy as np

def get_image_format(imagery):
    #TO-DO fix for non-mapbox imagery 
    o = urlparse(imagery)
    _, image_format = op.splitext(o.path)
    if not image_format in ['.png', '.jpg', '.jpeg']: 
        image_format =  '.png'
      
    return image_format

def url(tile, imagery):
    """Return a tile url provided an imagery template and a tile"""
    return imagery.replace('{x}', tile[0]).replace('{y}', tile[1]).replace('{z}', tile[2])


def download_tile_tms(tile, imagery, folder, zoom, supertile=False):
    """Download a satellite image tile from a tms endpoint"""

    image_format = get_image_format(imagery)
    r = requests.get(url(tile.split('-'), imagery))
    tile_img = op.join(folder, '{}{}'.format(tile, image_format))
    tile = tile.split('-')

    #super-tile special case
    if supertile:
        new_zoom = zoom + 1 #get zoom from ml-enabler database
        # get children
        child_tiles = children(int(tile[0]), int(tile[1]), int(tile[2]), zoom=new_zoom)
        child_tiles.sort()

        new_dim = 256 * (2 * zoom)

        w_lst = []
        for i in range (2 * zoom):
            for j in range(2 * zoom):
                window = Window(i * 256, j * 256, 256, 256)
                w_lst.append(window)

        # request children
        with rasterio.open(tile_img, 'w', driver='jpeg', height=new_dim,
                        width=new_dim, count=3, dtype=rasterio.uint8) as w:
                for num, t in enumerate(child_tiles):
                    t = [str(t[0]), str(t[1]), str(t[2])]
                    r = requests.get(url(t, imagery))
                    img = np.array(Image.open(io.BytesIO(r.content)), dtype=np.uint8)
                    try:
                        img = img.reshape((256, 256, 3)) # 4 channels returned from some endpoints, but not all
                    except ValueError:
                        img = img.reshape((256, 256, 4))
                    img = img[:, :, :3]
                    img = np.rollaxis(img, 2, 0)
                    w.write(img, window=w_lst[num])
    else:
        r = requests.get(url(tile, imagery))
        with open(tile_img, 'wb')as w:
            w.write(r.content)
    return tile_img

def download_img_match_labels(labels_folder, imagery, folder, zoom, supertile=False):
    #open the labels file and read the key (so we only download the images we have labels for)
    labels_file = op.join(labels_folder, 'labels.npz')
    tiles = np.load(labels_file)
    # create tiles directory
    tiles_dir = op.join(folder, 'tiles')
    if not op.isdir(tiles_dir):
        os.makedirs(tiles_dir)
    class_tiles = [tile for tile in tiles.files]
    #download images
    for tile in class_tiles:
        download_tile_tms(tile, imagery, folder, zoom, supertile=False)
        

# package up the images + labels into one data.npz file 
def make_datanpz(dest_folder, imagery, 
                    seed=False, 
                    split_names=('train', 'val', 'test'), 
                    split_vals=(0.7, .2, .1)):
    """Generate an .npz file containing arrays for training machine learning algorithms
    Parameters
    ------------
    dest_folder: str
        Folder to save labels, tiles, and final numpy arrays into
    imagery: str
        Imagery template to download satellite images from.
        Ex: http://a.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token=ACCESS_TOKEN
    seed: int
        Random generator seed. Optional, use to make results reproducible.
    split_vals: tuple
        Percentage of data to put in each catagory listed in split_names. Must
        be floats and must sum to one. Default: (0.8, 0.2)
    split_names: tupel
        Default: ('train', 'test')
        List of names for each subset of the data.
    """
    # if a seed is given, use it
    if seed:
        np.random.seed(seed)

    if len(split_names) != len(split_vals):
        raise ValueError('`split_names` and `split_vals` must be the same '
                            'length. Please update your config.')
    if not np.isclose(sum(split_vals), 1):
        raise ValueError('`split_vals` must sum to one. Please update your config.')

    # open labels file, create tile array
    labels_file = op.join(dest_folder, 'labels.npz')
    labels = np.load(labels_file)
    tile_names = [tile for tile in labels.files]
    tile_names.sort()
    tiles = np.array(tile_names)
    np.random.shuffle(tiles)


    # open the images and load those plus the labels into the final arrays
    image_format = get_image_format(imagery)
    print(image_format)

    x_vals = []
    y_vals = []

    for tile in tiles:
        image_file = op.join(dest_folder, 'tiles', '{}{}'.format(tile, image_format))
        try:
            img = Image.open(image_file)
        except FileNotFoundError:
            # we often don't download images for each label (e.g. background tiles)
            continue
        except OSError:
            print('Couldn\'t open {}, skipping'.format(image_file))
            continue

        np_image = np.array(img)
        img.close()

        #focusing just on classification
        x_vals.append(np_image)
        y_vals.append(labels[tile])

    # Convert lists to numpy arrays
    x_vals = np.array(x_vals, dtype=np.uint8)
    y_vals = np.array(y_vals, dtype=np.uint8)

    # Get number of data samples per split from the float proportions
    split_n_samps = [len(x_vals) * val for val in split_vals]

    if np.any(split_n_samps == 0):
        raise ValueError('Split must not generate zero samples per partition. '
                            'Change ratio of values in config file.')

    # Convert into a cumulative sum to get indices
    split_inds = np.cumsum(split_n_samps).astype(np.integer)

    # Exclude last index as `np.split` handles splitting without that value
    split_arrs_x = np.split(x_vals, split_inds[:-1])
    split_arrs_y = np.split(y_vals, split_inds[:-1])

    save_dict = {}

    for si, split_name in enumerate(split_names):
        save_dict['x_{}'.format(split_name)] = split_arrs_x[si]
        save_dict['y_{}'.format(split_name)] = split_arrs_y[si]

    np.savez(op.join(dest_folder, 'data.npz'), **save_dict)
    print('Saving packaged file to {}'.format(op.join(dest_folder, 'data.npz')))