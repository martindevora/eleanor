import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import warnings
import lightkurve as lk

from .ffi import use_pointing_model, load_pointing_model
from .mast import *

__all__ = []


class Visualize(object):
    """
    The main class for creating figures, movies, and interactive plots.
    Allows the user to have a grand ole time playing with their data!

    Parameters
    ----------
    obj :
        Object must have minimum attributes of 2D array of flux.
        Will allow for plotting of both postcards & tpfs.
    obj_type :
        Object type can be set to "tpf" or "postcard". Default is "tpf".
    """

    def __init__(self, object, obj_type="tpf"):
        self.obj      = object
        self.obj_type = obj_type.lower()

        if self.obj_type == "tpf":
            self.flux   = self.obj.tpf
            self.center = (np.nanmedian(self.obj.centroid_xs),
                             np.nanmedian(self.obj.centroid_ys))
            self.dimensions = self.obj.tpf[0].shape
        else:
            self.flux   = self.obj.flux
            self.center = self.obj.center_xy
            self.dimensions = self.obj.dimensions



    def pixel_by_pixel(self, colrange=None, rowrange=None,
                       data_type="corrected", mask=None):
        """
        Creates a pixel-by-pixel light curve using the corrected flux.

        Parameters
        ----------
        colrange : np.array, optional
             A list of start column and end column you're interested in
             zooming in on.
        rowrange : np.array, optional
             A list of start row and end row you're interested in zooming
             in on.
        data_type : str, optional
             The type of flux used. Either: 'raw', 'corrected' or 'amplitude'.
             If not, default set to 'corrected'.
        mask : np.array, optional
             Specifies the cadences used in the light curve. If not, default
             set to good quality cadences.
        """
        if colrange is None:
            colrange = [0, self.dimensions[0]]

        if rowrange is None:
            rowrange = [0, self.dimensions[1]]


        nrows = int(np.round(colrange[1]-colrange[0]))
        ncols = int(np.round(rowrange[1]-rowrange[0]))

        if (colrange[1] > self.dimensions[1]) or (rowrange[1] > self.dimensions[0]):
            raise ValueError("Asking for more pixels than available in the TPF.")


        figure = plt.figure(figsize=(20,8))
        outer = gridspec.GridSpec(1,2, width_ratios=[1,4])

        inner = gridspec.GridSpecFromSubplotSpec(nrows, ncols, hspace=0.1, wspace=0.1,
                                                 subplot_spec=outer[1])

        i, j = rowrange[0], colrange[0]

        if mask is None:
            q = self.obj.quality == 0
        else:
            q = mask == 0

        for ind in range( int(nrows * ncols) ):
            ax = plt.Subplot(figure, inner[ind])

            y = self.flux[:,i,j]
            x = self.obj.time

            if data_type.lower() == 'corrected':
                y = self.obj.corrected_flux(flux=y)
                y = y[q]/np.nanmedian(y[q])
                x = x[q]

            elif data_type.lower() == 'amplitude':
                pg = lk.LightCurve(time=x, flux=y).to_periodogram()
                x = pg.frequency.value
                y = pg.power.value

            elif data_type.lower() == 'raw':
                y = y[q]/np.nanmedian(y[q])
                x = x[q]

            ax.plot(x, y, 'k')

            j += 1
            if j == colrange[1]:
                i += 1
                j  = colrange[0]

            ax.set_ylim(np.percentile(y, 1), np.percentile(y, 99))

            ax.set_xlim(np.min(x)-0.1,
                        np.max(x)+0.1)

            if data_type.lower() == 'amplitude':
                ax.set_yscale('log')
                ax.set_xscale('log')
                ax.set_ylim(y.min(), y.max())
                ax.set_xlim(np.min(x),
                            np.max(x))

            ax.set_xticks([])
            ax.set_yticks([])

            figure.add_subplot(ax)

        ax = plt.subplot(outer[0])
        c = ax.imshow(self.flux[0, colrange[0]:colrange[1],
                                rowrange[0]:rowrange[1]],
                      vmax=np.percentile(self.flux[0], 95))
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.15)
        plt.colorbar(c, cax=cax, orientation='vertical')

        figure.show()
