"""Visualization tools"""
#From https://gist.github.com/jakevdp/91077b0cae40f8f8244a
import matplotlib.pyplot as plt
import numpy as np
from skimage import exposure

def plot_prediction(image, label, prediction, ls_pct=5):
    """Plot an image with labels, optionally create a three band composite
    Args:
        image: a rgb or multiband image
        label: true class
        prediction: predicted class
        ls_pct: linear stretch of three band
    """
    fig = plt.figure()    
    ax = fig.add_subplot(111)
    
    #check if hyperspec and create three band false color.
    if image.shape[2] > 3:
        image = image[:,:,[11, 55, 113]]        
        pLow, pHigh = np.percentile(image[~np.isnan(image)], (ls_pct,100-ls_pct))
        image = exposure.rescale_intensity(image, in_range=(pLow,pHigh))
                
    ax.imshow(image.astype(int))
    ax.set_title("True: {}, Predicted: {} ".format(label, prediction))
    
    return fig

def create_raster(results):
    """Reshape a set of predictions from DeepTreeAttention.predict into a raster image"""
    #Create image
    rowIDs = results['row']
    colIDs = results['col']
    predicted_raster = np.zeros((rowIDs.max() + 1, colIDs.max() + 1))
    predicted_raster[rowIDs, colIDs] = results["label"]
    predicted_raster = predicted_raster.astype("uint16")

    return predicted_raster


def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)
