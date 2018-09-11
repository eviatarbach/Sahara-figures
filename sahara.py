import cartopy.crs as ccrs
import cartopy.util
import matplotlib.pyplot as plt
import numpy
import xarray
import cmocean
import scipy.ndimage

import numpy as np
import matplotlib
from matplotlib.patches import Patch
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


def shiftedColorMap(cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
    '''
    From https://gist.github.com/phobson/7916777

    Function to offset the "center" of a colormap. Useful for
    data with a negative min and positive max and you want the
    middle of the colormap's dynamic range to be at zero

    Input
    -----
      cmap : The matplotlib colormap to be altered
      start : Offset from lowest point in the colormap's range.
          Defaults to 0.0 (no lower ofset). Should be between
          0.0 and 1.0.
      midpoint : The new center of the colormap. Defaults to
          0.5 (no shift). Should be between 0.0 and 1.0. In
          general, this should be  1 - vmax/(vmax + abs(vmin))
          For example if your data range from -15.0 to +5.0 and
          you want the center of the colormap at 0.0, `midpoint`
          should be set to  1 - 5/(5 + 15)) or 0.75
      stop : Offset from highets point in the colormap's range.
          Defaults to 1.0 (no upper ofset). Should be between
          0.0 and 1.0.
    '''
    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(start, stop, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False),
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        if (ri > 0.49) and (ri < 0.51):
            a = 0.2
            cdict['red'].append((si, r, r))
            cdict['green'].append((si, g, g))
            cdict['blue'].append((si, b, b))
            cdict['alpha'].append((si, a, a))
        else:
            cdict['red'].append((si, r, r))
            cdict['green'].append((si, g, g))
            cdict['blue'].append((si, b, b))
            cdict['alpha'].append((si, a, a))

    newcmap = matplotlib.colors.LinearSegmentedColormap(name, cdict)
    plt.register_cmap(cmap=newcmap)

    return newcmap


# Choose colormap
cmap = cmocean.cm.balance_r
cmap = shiftedColorMap(cmap, start=2/8, midpoint=4/8, stop=1, name='shrunk')

ds = xarray.open_dataset('ExpWindSolar0_prec_diff.nc')

ax = plt.subplot(1, 1, 1, projection=ccrs.PlateCarree())
ax.coastlines()
dat, lon2 = cartopy.util.add_cyclic_point(ds.difference_of_prec.values,
                                          coord=ds.lon)
dat3 = dat.copy()
dat3[numpy.isnan(dat3)] = 0
lat = numpy.linspace(ds.lat.min(), ds.lat.max(), len(ds.lat)*2)
lon = numpy.linspace(lon2.min(), lon2.max(), len(lon2)*2)
dat2 = scipy.ndimage.zoom(dat3, 2, order=2, prefilter=True)
rep = numpy.repeat(numpy.repeat(dat, 2, axis=0), 2, axis=1)
dat2[numpy.isnan(rep)] = 0
lon, lat = numpy.meshgrid(lon, lat)
plt.contourf(lon, lat, dat2, transform=ccrs.PlateCarree(), cmap=cmap,
             levels=sorted(numpy.hstack([numpy.linspace(-4, 4, 17)[4:],
                                         -0.2e-2, 0.2e-2])), antialiased=True)
cbar = plt.colorbar(ticks=numpy.arange(-2, 5), orientation='horizontal',
                    fraction=0.056, pad=0.12, spacing='proportional')
cbar.set_label('Rainfall change (mm/day)')
ax.set_extent([-25, 55, -2, 39], ccrs.PlateCarree())
plt.title('Modeled rain impact of large-scale wind and solar\n'
          'farms in the Sahara')
leg = ax.legend(handles=[Patch(facecolor='w', edgecolor='black',
                               label='Not significant')],
                bbox_to_anchor=(0.32, -0.42), loc=2)
leg.get_frame().set_linewidth(0.0)
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=2, color='gray', alpha=0, linestyle='--')
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER
gl.xlabels_top = False
gl.ylabels_right = False
plt.savefig('precip.pdf', dpi=600, bbox_inches="tight")
