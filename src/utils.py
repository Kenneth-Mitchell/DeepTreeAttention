#data utils
import argparse
import json
import os
import numpy as np
from torchvision import transforms
import torch.nn.functional as F
from sklearn import preprocessing
import torch
import yaml
import warnings
import pandas as pd
from torch.utils.data.dataloader import default_collate
from glob import glob
import rasterio as rio


def read_config(config_path):
    """Read config yaml file"""
    #Allow command line to override 
    parser = argparse.ArgumentParser("DeepTreeAttention config")
    parser.add_argument('-d', '--my-dict', type=json.loads, default=None)
    args = parser.parse_known_args()
    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    except Exception as e:
        raise FileNotFoundError("There is no config at {}, yields {}".format(
            config_path, e))
    
    #Update anything in argparse to have higher priority
    if args[0].my_dict:
        for key, value in args[0].my_dict:
            config[key] = value
        
    return config

def create_glob_lists(config):
    """Creating glob lists is expensive, do it only once at the beginning of the run."""
    rgb_pool = glob(config["rgb_sensor_pool"], recursive=True)
    #rgb_pool = [x for x in rgb_pool if "neon-aop-products" not in x]
    rgb_pool = [x for x in rgb_pool if "classified" not in x]    
    rgb_pool = [x for x in rgb_pool if not "point_cloud" in x]
    rgb_pool = [x for x in rgb_pool if not "UTM" in x]

    
    h5_pool = glob(config["HSI_sensor_pool"], recursive=True)
    h5_pool = [x for x in h5_pool if not "point_cloud" in x]
    
    
    hsi_pool = glob("{}/**/*.tif".format(config["HSI_tif_dir"]),recursive=True)
    try:
        CHM_pool = glob(config["CHM_pool"], recursive=True)
    except:
        CHM_pool = None
    
    return rgb_pool, h5_pool, hsi_pool, CHM_pool

def preprocess_image(image, channel_is_first=False):
    """Preprocess a loaded image, if already C*H*W set channel_is_first=True"""
    
    #Clip first and last 10 bands
    if image.shape[0] > 3:
        image = image[10:,:,:]
        image = image[:-10,:,:]
        
    img = np.asarray(image, dtype='float32')
    data = img.reshape(img.shape[0], np.prod(img.shape[1:])).T
    
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)    
        data  = preprocessing.minmax_scale(data, axis=1).T
    img = data.reshape(img.shape)
    
    if not channel_is_first:
        img = np.rollaxis(img, 2,0)
        
    normalized = torch.from_numpy(img)
    
    return normalized

class ZeroPad(object):
    def __init__(self, target_size):
        self.target_size = target_size

    def __call__(self, sample):
        img = sample

        # Get the original image size, allow for batch dim, just take last two positions
        img_height, img_width = img.size()[-2:]

        # Calculate the padding amounts on all sides
        pad_height = self.target_size - img_height
        pad_width = self.target_size - img_width

        left = int(pad_width/2)
        right = self.target_size - img_width - left

        top = int(pad_height/2)
        bottom = self.target_size - img_height - top

        # Apply zero padding using torch.nn.functional.pad
        img = F.pad(img, (left, right, top, bottom), value=0)

        return img

def load_image(img_path=None, allow_NA=False):
    """Load and preprocess an image for training/prediction
    Args:
        img_path (str): path to .npy or .tif on disk
        allow_NA (bool): If False, return ValueError when encountering -9999"""
    if os.path.splitext(img_path)[-1] == ".npy":
        try:
            image = np.load(img_path)
        except:
            raise ValueError("Cannot load {}".format(img_path))
        
    elif os.path.splitext(img_path)[-1] == ".tif":   
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', rio.errors.NotGeoreferencedWarning)
            image = rio.open(img_path).read()
    else:
        raise ValueError("image path must be .npy or .tif, found {}".format(img_path))

    if not allow_NA:
        if (image == -9999).any():
            raise ValueError("Input image path {} had NA value of -9999".format(img_path))
         
    image = preprocess_image(image, channel_is_first=True)
    
    return image

def my_collate(batch):
    batch = [x for x in batch if x[1]["HSI"] is not None]
    
    return default_collate(batch)

def skip_none_collate(batch):
    batch = [x for x in batch if x is not None]
    batch = [x for x in batch if not all(image.sum() == 0 for year,image in x[1]["HSI"].items())]
    
    if len(batch) == 0:
        return None
    
    return default_collate(batch)    

def skip_none_dead_collate(batch):
    batch = [x for x in batch if x is not None]
    
    if len(batch) == 0:
        return None
    
    return default_collate(batch)  

def predictions_to_df(predictions):
    """format a dataframe"""
    individuals = np.concatenate([x[0] for x in predictions])
    predictions = np.concatenate([x[1] for x in predictions])
    predictions = pd.DataFrame(predictions.squeeze())
    predictions["individual"] = individuals    
    
    return predictions

def preload_image_dict(df, config):
    """Load an entire dataset into memory and place it on device. This is useful for point to objects already in memory
    Args:
        df: a pandas dataframe with individual, tile_year and image_path columns for each image on disk
        config: a DeepTreeAttention config
    """
    years = df.tile_year.unique()    
    individuals = df.individual.unique()
    image_paths = df.groupby("individual").apply(lambda x: x.set_index('tile_year').image_path.to_dict())    
    image_dict = { }
    for individual in individuals:
        images = { }
        ind_annotations = image_paths[individual]
        for year in years:
            try:
                year_annotations = ind_annotations[year]
            except KeyError:
                images[str(year)] = image = torch.zeros(config["bands"], config["image_size"],  config["image_size"])  
                continue
            image_path = os.path.join(config["crop_dir"], year_annotations)
            try:
                image = load_image(image_path)   
            except ValueError:
                image = torch.zeros(config["bands"], config["image_size"],  config["image_size"])                             
            images[str(year)] = image
        image_dict[individual] = images 
    
    return image_dict

