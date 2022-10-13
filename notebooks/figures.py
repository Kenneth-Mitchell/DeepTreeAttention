# Figure 1, spectra, RGB and HSI side by side plot
from src import data
from src import neon_paths
from src import utils
import os
import numpy as np
from matplotlib import pyplot as plt
import rasterio
import glob
from descartes import PolygonPatch
from matplotlib.collections import PatchCollection
from rasterio.plot import show

config = data.read_config("config.yml")
config["crop_dir"] = os.path.join(config["data_dir"], config["use_data_commit"])

data_module = data.TreeData(
    csv_file="data/raw/neon_vst_data_2022.csv",
    data_dir=config["crop_dir"],
    config=config,
    client=None,
    metadata=True,
    comet_logger=None)

def plot_spectra(individualID, df, crop_dir):
    """Create pixel spectra figures from a results object
    Args:
       df: pandas dataframe generated by main.predict_dataloader
    """
    row = df[df.individualID==individualID].iloc[0]
    HSI_path = os.path.join(crop_dir,"{}".format(row["image_path"]))
    hsi_sample = utils.load_image(img_path=HSI_path, image_size=11)
    for x in hsi_sample.reshape(hsi_sample.shape[0], np.prod(hsi_sample.shape[1:])).T:
        plt.plot(x)
    
    plt.savefig("results/{}_spectra.png".format(row["individualID"]))            
    plt.close()
        
def plot_crowns(individual, crowns, points, sensor_pool, suffix=None):
    fig = plt.figure(0)
    ax = fig.add_subplot(1, 1, 1)                
    geom = crowns[crowns.individual == individual].geometry.iloc[0]
    left, bottom, right, top = geom.bounds
    
    #Find image
    img_path = neon_paths.find_sensor_path(lookup_pool=sensor_pool, bounds=geom.bounds)
    src = rasterio.open(img_path)
    res = src.res[0]
    img = src.read(window=rasterio.windows.from_bounds(left-10, bottom-10, right+10, top+10, transform=src.transform))  
    img_transform = src.window_transform(window=rasterio.windows.from_bounds(left-10, bottom-10, right+10, top+10, transform=src.transform))  
    
    #Plot crown
    patches = [PolygonPatch(geom, edgecolor='red', facecolor='none')]
    if suffix == "HSI":
        scale = np.quantile(img[(11,55,113),:,:],0.9, axis=(1,2))
        img_scaled = img[(11,55,113),:,:] / scale[:,np.newaxis, np.newaxis]
        img_scaled = img_scaled* 255
        show(img_scaled.astype(int), ax=ax, transform=img_transform)       
    else:
        show(img[:,:,:], ax=ax, transform=img_transform)                
        
    ax.add_collection(PatchCollection(patches, match_original=True))
    
    #Plot field coordinate
    stem = points[points.individualID == individual]
    stem.plot(ax=ax)
    
    image_name = "results/{}_{}.png".format(individual, suffix)
    plt.tick_params(left=False,bottom=False)
    plt.axis("off") 
    plt.savefig(image_name)
    src.close()
    plt.close("all")
    
rgb_pool = glob.glob(config["rgb_sensor_pool"], recursive=True)
hsi_pool = glob.glob(config["HSI_tif_dir"]+"/*", recursive=True)

PIPA2 = data_module.test[data_module.test.taxonID=="PIPA2"].individualID.iloc[0]
plot_crowns(PIPA2, data_module.crowns, data_module.canopy_points, rgb_pool, suffix="RGB")
plot_crowns(PIPA2, data_module.crowns, data_module.canopy_points, hsi_pool, suffix="HSI")
plot_spectra(PIPA2, df=data_module.test, crop_dir=config["crop_dir"])

QULA2 = data_module.test[data_module.test.taxonID=="QULA2"].individualID.iloc[0]
plot_crowns(QULA2, data_module.crowns, data_module.canopy_points, rgb_pool, suffix="RGB")
plot_crowns(QULA2, data_module.crowns, data_module.canopy_points, hsi_pool, suffix="HSI")
plot_spectra(QULA2, df=data_module.test, crop_dir=config["crop_dir"])

CAGL8 = data_module.test[data_module.test.taxonID=="CAGL8"].individualID.iloc[5]
plot_crowns(CAGL8, data_module.crowns, data_module.canopy_points, rgb_pool, suffix="RGB")
plot_crowns(CAGL8, data_module.crowns, data_module.canopy_points, hsi_pool, suffix="HSI")
plot_spectra(CAGL8, df=data_module.test, crop_dir=config["crop_dir"])
