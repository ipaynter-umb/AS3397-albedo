import h5py
from pathlib import Path
from os import environ, mkdir
from os.path import exists
import dotenv
import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns

# Load the environmental variables
dotenv.load_dotenv()

# Set matplotlib defaults for fonts
mpl.rc('font', family='Times New Roman')
mpl.rc('axes', labelsize=14)
mpl.rc('axes', titlesize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)


# Main function
def main(vnp_file_name, vj1_file_name, albedo_sat, save_figs=False, show_figs=True):

    # Open the vnp and vj1 files as h5py File objects
    vnp_file = h5py.File(Path(environ['output_files_path'] + vnp_file_name))
    vj1_file = h5py.File(Path(environ['output_files_path'] + vj1_file_name))

    # Split out the product, tile name and the date
    split_name = vnp_file_name.split('.')
    tile = split_name[2]
    year = split_name[1][1:5]
    doy = split_name[1][5:8]
    product = split_name[0][3:]
    # Establish the keywords and scale factor for the product
    keyword = "Albedo"
    figure_keyword = "Albedo"
    scale_factor = 0.001
    if product == "43MA4":
        keyword = "Nadir"
        figure_keyword = "NBAR"
        scale_factor = 0.0001

    # Path for results
    results_path = Path(environ['output_files_path'] + f'{product}_{year}_{doy}_{tile}/')

    # If there is no directory for these results
    if not exists(results_path):
        # Make one
        mkdir(results_path)

    # Get a colormap object for the percent diffs
    perc_norm = mpl.colors.Normalize(vmin=-0.1, vmax=0.1)
    cmap = mpl.cm.get_cmap("seismic").copy()
    cmap.set_bad('k')
    perc_cmap = mpl.cm.ScalarMappable(cmap=cmap, norm=perc_norm)

    # For each key (band)
    for key in vnp_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'].keys():
        # If the key begins with the product keyword
        if key.split('_')[0] == keyword:

            # Get the arrays for the specific band
            vnp_array = np.array(vnp_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'][key])
            vj1_array = np.array(vj1_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'][key])

            # Swap the fill values (32767 for signed 16 bit integer) for numpy NaN values
            vnp_filter_array = np.where(vnp_array != 32767, vnp_array, np.nan)
            vj1_filter_array = np.where(vj1_array != 32767, vj1_array, np.nan)

            # Get the quality flag band key
            quality_key = f'BRDF_Albedo_Band_Mandatory_Quality_' + key.split('_')[-1]

            # Get the quality flag arrays for the band
            vnp_qual = np.array(vnp_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'][quality_key])
            vj1_qual = np.array(vj1_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'][quality_key])

            # Swap the low quality values (>0 in the quality flags) for numpy NaN values
            vnp_filter_array = np.where(vnp_qual == 0, vnp_filter_array, np.nan)
            vj1_filter_array = np.where(vj1_qual == 0, vj1_filter_array, np.nan)

            # Subtract the VJ1 band values from the SNPP values, apply scale factor
            diff_array = np.multiply(np.subtract(vnp_filter_array, vj1_filter_array), scale_factor)

            # Calculate the percent difference (relative to VNP)
            #perc_diff = np.where(vnp_filter_array != 0, np.multiply(np.divide(diff_array, vnp_filter_array), 100), 0)

            # Transform to a 1D arrays
            #oned_diff = np.reshape(perc_diff, perc_diff.shape[0] * perc_diff.shape[1])
            oned_diff = np.reshape(diff_array, diff_array.shape[0] * diff_array.shape[1])

            # Apply the scale factors
            vnp_filter_array = np.multiply(vnp_filter_array, scale_factor)
            vj1_filter_array = np.multiply(vj1_filter_array, scale_factor)

            # Transform to a 1D arrays
            oned_vnp = np.reshape(vnp_filter_array, vnp_filter_array.shape[0] * vnp_filter_array.shape[1])
            oned_vj1 = np.reshape(vj1_filter_array, vj1_filter_array.shape[0] * vj1_filter_array.shape[1])

            # Get the overall max and mins between the arrays
            overall_max = max(np.nanmax(vnp_filter_array), np.nanmax(vj1_filter_array))
            overall_min = min(np.nanmin(vnp_filter_array), np.nanmin(vj1_filter_array))

            # Get a colormap object
            norm = mpl.colors.Normalize(vmin=0, vmax=albedo_sat)
            cmap = mpl.cm.get_cmap("seismic").copy()
            cmap.set_bad('k')
            my_cmap = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

            # Plot the data
            fig = plt.figure(figsize=(16, 10))
            ax = fig.add_subplot(2, 3, 1)
            ax.imshow(vnp_filter_array, cmap=my_cmap.cmap, norm=norm)
            ax.set_title(f"VNP{product}")
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            #ax.axis('off')

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(my_cmap, cax=cax)

            ax = fig.add_subplot(2, 3, 2)
            ax.imshow(vj1_filter_array, cmap=my_cmap.cmap, norm=norm)
            ax.set_title(f"Layer: {key}, Tile: {tile}, Year: {year}, DOY: {doy} \n\n VJ1{product}")
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            # ax.axis('off')

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(my_cmap, cax=cax)

            ax = fig.add_subplot(2, 3, 3)
            ax.imshow(diff_array, cmap=perc_cmap.cmap, norm=perc_norm)
            ax.set_title(f"Difference (VNP{product} - VJ1{product})")
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            # ax.axis('off')

            # create an axes on the right side of ax. The width of cax will be 5%
            # of ax and the padding between cax and ax will be fixed at 0.05 inch.
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = plt.colorbar(perc_cmap, cax=cax, ticks=[-0.1, 0, 0.1])
            #plt.colorbar(perc_cmap, fraction=0.046, pad=0.04)
            cbar.ax.set_yticklabels(['< -0.1', '0', '> +0.1'])

            # Overlaid density plot
            ax = fig.add_subplot(2, 3, 4)

            # Bandwidth for smoothing
            bandwidth = 0.5

            sns.kdeplot(oned_vnp,
                        ax=ax,
                        x=figure_keyword,
                        fill=True,
                        bw_adjust=bandwidth)

            sns.kdeplot(oned_vj1,
                        ax=ax,
                        x=figure_keyword,
                        fill=True,
                        bw_adjust=bandwidth)

            ax.set_xlabel(figure_keyword)
            ax.set_title(f"Kernel Density Estimates (bandwidth: {bandwidth})")
            plt.legend(labels=[f"VNP{product}", f"VJ1{product}"])

            # Complicated hexbin + histograms plot
            ax = fig.add_subplot(2, 3, 5)
            ax.axis('off')
            # for key in ax.__dict__:
            #     print(key, ax.__dict__.get(key))
            #print(ax.__dict__['_position'])
            # exit()

            hist_size = 0.03

            # definitions for the hexbin plot axes
            left, width = ax.__dict__['_position'].x0, ax.__dict__['_position'].x1 - ax.__dict__['_position'].x0 - hist_size
            bottom, height = ax.__dict__['_position'].y0, ax.__dict__['_position'].y1 - ax.__dict__['_position'].y0 - hist_size
            spacing = 0.002

            rect_hexbin = [left, bottom, width, height]
            rect_histx = [left, bottom + height + spacing, width, hist_size]
            rect_histy = [left + width + spacing, bottom, hist_size, height]

            ax_hexbin = plt.axes(rect_hexbin)
            # Get a colormap object for the hex bins
            hex_norm = mpl.colors.Normalize(vmin=1, vmax=5000)
            cmap = mpl.cm.get_cmap("jet").copy()
            cmap.set_bad('k')
            cmap.set_under('white')
            hex_cmap = mpl.cm.ScalarMappable(cmap=cmap, norm=hex_norm)

            ax_hexbin.hexbin(oned_vnp, oned_vj1, gridsize=50, cmap=hex_cmap.cmap, norm=hex_norm)
            ax_hexbin.plot([0, overall_max], [0, overall_max], 'k', linestyle='--')
            ax_hexbin.set_xlim(overall_min, overall_max)
            ax_hexbin.set_ylim(overall_min, overall_max)
            ax_hexbin.set_xlabel(f'VNP{product} {figure_keyword}')
            ax_hexbin.set_ylabel(f'VJ{product} {figure_keyword}')

            ax.tick_params(direction='in', top=True, right=True)
            ax_histx = plt.axes(rect_histx)
            ax_histx.tick_params(direction='in', labelbottom=False)
            ax_histx.axis('off')
            ax_histy = plt.axes(rect_histy)
            ax_histy.tick_params(direction='in', labelleft=False)
            ax_histy.axis('off')

            # now determine nice limits by hand:
            binwidth = 0.25
            #lim = np.ceil(np.abs([x, y]).max() / binwidth) * binwidth
            #ax_scatter.set_xlim((-lim, lim))
            #ax_scatter.set_ylim((-lim, lim))

            #bins = np.arange(-lim, lim + binwidth, binwidth)
            ax_histx.hist(oned_vnp, bins=np.arange(0, 1, 0.025), rwidth=0.9, color='dimgrey')
            ax_histy.hist(oned_vj1, bins=np.arange(0, 1, 0.025), orientation='horizontal', rwidth=0.9, color='dimgrey')

            ax_histx.set_xlim(ax_hexbin.get_xlim())
            ax_histy.set_ylim(ax_hexbin.get_ylim())

            ax = fig.add_subplot(2, 3, 6)
            grid = ax.grid(which='major', axis='y', zorder=0)
            ax.hist(oned_diff, bins=np.arange(-1, 1, 0.05), weights=np.zeros_like(oned_diff) + 1. / oned_diff.size, color='dimgrey', zorder=3)
            ax.set_xlim(np.nanmin(oned_diff), np.nanmax(oned_diff))
            ax.set_xlabel(f"Difference (VNP{product} - VJ1{product})")
            ax.set_ylabel(f"Frequency")

            # If saving figures
            if save_figs:
                plt.savefig(Path(str(results_path) + f'/{key}.png'), dpi='figure', format='png')
            # If showing figures
            if show_figs:
                plt.show()
            # Close figure
            plt.close()



if __name__ == '__main__':

    # USER-DEFINED INPUTS
    # VNP file name
    vnp_file = 'VNP43MA4.A2021201.h17v01.002.2022121145105.h5'
    # VJ1 file name
    vj1_file = 'VJ143MA4.A2021201.h17v01.002.2022153174223.h5'
    # Albedo saturation value for plots
    albedo_sat = 1
    # Show figures? True/False
    show_figures = False
    # Save the figures? True/False
    save_figures = True

    # END USER INPUTS

    # Call main function
    main(vnp_file, vj1_file, albedo_sat, save_figs=save_figures, show_figs=show_figures)
