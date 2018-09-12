import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy
import xarray
import cmocean
import scipy.ndimage


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
    reg_index = numpy.linspace(start, stop, 257)

    # shifted index to match the data
    shift_index = numpy.hstack([
        numpy.linspace(0.0, midpoint, 128, endpoint=False),
        numpy.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    newcmap = LinearSegmentedColormap(name, cdict)
    plt.register_cmap(cmap=newcmap)

    return newcmap


cmap = cmocean.cm.balance_r
cmap = shiftedColorMap(cmap, start=4/12, midpoint=6/12, stop=1, name='shrunk')

ds = xarray.open_dataset('ExpWindSolar0_prec_diff.nc')
ds_ctl = xarray.open_dataset('attm_ctl.nc')
ctl_prec = (ds_ctl['precls'] + ds_ctl['precnv'])[50*12:].mean('time')
ds.difference_of_prec.values[numpy.isnan(ds.difference_of_prec.values)] = 0
dat_relative = 100*ds.difference_of_prec.values/ctl_prec.values

ax = plt.subplot(1, 1, 1, projection=ccrs.PlateCarree())
ax.coastlines()

# Avoid discontinuity at the prime meridian
dat, lon_cyc = add_cyclic_point(dat_relative, coord=ds.lon)

# Smooth contours by zooming
lat_zoom = numpy.linspace(ds.lat.min(), ds.lat.max(), len(ds.lat)*2)
lon_zoom = numpy.linspace(lon_cyc.min(), lon_cyc.max(), len(lon_cyc)*2)
dat_zoom = scipy.ndimage.zoom(dat, 2)

plt.contourf(lon_zoom, lat_zoom, dat_zoom, transform=ccrs.PlateCarree(),
             cmap=cmap, levels=numpy.linspace(-200, 600, 33), antialiased=True)

cbar = plt.colorbar(ticks=range(-200, 700, 100), orientation='horizontal',
                    fraction=0.056, pad=0.12, spacing='proportional')
cbar.set_label('Rainfall change (%)')
ax.set_extent([-25, 55, -2, 39], ccrs.PlateCarree())
plt.title('Modeled rain impact of large-scale wind and solar\n'
          'farms in the Sahara')
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=2, color='gray', alpha=0, linestyle='--')
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER
gl.xlabels_top = False
gl.ylabels_right = False

plt.savefig('precip_relative.pdf', bbox_inches="tight")
