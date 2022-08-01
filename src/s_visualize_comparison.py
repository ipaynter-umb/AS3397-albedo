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
    # <> support dictionary?
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

            # Transform to a 1D arrays
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

            # PLOTTING DATA

            # Get a colormap object
            norm = mpl.colors.Normalize(vmin=0, vmax=albedo_sat)
            cmap = mpl.cm.get_cmap("seismic").copy()
            cmap.set_bad('black')
            my_cmap = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)

            # Establish figure
            fig = plt.figure(figsize=(16, 10))

            # Subplot 1: VNP map
            ax = fig.add_subplot(2, 3, 1)
            ax.imshow(vnp_filter_array, cmap=my_cmap.cmap, norm=norm)
            ax.set_title(f"VNP{product}")
            # Make the tick marks invisible
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            # Set up the colorbar by dividing the subplot with an extra axis
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(my_cmap, cax=cax)

            # Subplot 2: VJ1 map
            ax = fig.add_subplot(2, 3, 2)
            ax.imshow(vj1_filter_array, cmap=my_cmap.cmap, norm=norm)
            ax.set_title(f"Layer: {key}, Tile: {tile}, Year: {year}, DOY: {doy} \n\n VJ1{product}")
            # Make the tick marks invisible
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            # Set up the colorbar by dividing the subplot with an extra axis
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(my_cmap, cax=cax)

            # Subplot 3: Difference map
            ax = fig.add_subplot(2, 3, 3)
            ax.imshow(diff_array, cmap=perc_cmap.cmap, norm=perc_norm)
            ax.set_title(f"Difference (VNP{product} - VJ1{product})")
            # Make the tick marks invisible
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            # Set up the colorbar by dividing the subplot with an extra axis
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = plt.colorbar(perc_cmap, cax=cax, ticks=[-0.1, 0, 0.1])
            # Set custom tick labels for the colorbar
            cbar.ax.set_yticklabels(['< -0.1', '0', '> +0.1'])

            # Subplot 4: Kernel Density Plot
            ax = fig.add_subplot(2, 3, 4)
            # Bandwidth for smoothing
            bandwidth = 0.5
            # Add VNP data
            sns.kdeplot(oned_vnp,
                        ax=ax,
                        x=figure_keyword,
                        fill=True,
                        bw_adjust=bandwidth)
            # Add VJ1 data
            sns.kdeplot(oned_vj1,
                        ax=ax,
                        x=figure_keyword,
                        fill=True,
                        bw_adjust=bandwidth)
            # Set axis label and title
            ax.set_xlabel(figure_keyword)
            ax.set_title(f"Kernel Density Estimates (bandwidth: {bandwidth})")
            # Add legend
            plt.legend(labels=[f"VNP{product}", f"VJ1{product}"])

            # Subplot 5: Complicated hexbin + histograms plot
            ax = fig.add_subplot(2, 3, 5)
            # Turn off original axis for subplot (we're just going to use the space)
            ax.axis('off')
            # Histogram size (height for top histogram, width for right histogram)
            hist_size = 0.03
            # Space between each histogram and axis
            spacing = 0.002

            # Definitions for the hexbin plot axes based on spatial properties of the subplot
            left = ax.__dict__['_position'].x0
            width = ax.__dict__['_position'].x1 - ax.__dict__['_position'].x0 - hist_size
            bottom = ax.__dict__['_position'].y0
            height = ax.__dict__['_position'].y1 - ax.__dict__['_position'].y0 - hist_size

            # Define the three plot spaces
            rect_hexbin = [left, bottom, width, height]
            rect_histx = [left, bottom + height + spacing, width, hist_size]
            rect_histy = [left + width + spacing, bottom, hist_size, height]

            # Get axes corresponding to the hexbin space
            ax_hexbin = plt.axes(rect_hexbin)
            # Get a colormap object for the hex bins
            hex_norm = mpl.colors.Normalize(vmin=1, vmax=5000)
            cmap = mpl.cm.get_cmap("jet").copy()
            # Set bad (np.nan) and under (< vmin) colors
            cmap.set_bad('k')
            cmap.set_under('white')
            # Form a colormap based on the normalization
            hex_cmap = mpl.cm.ScalarMappable(cmap=cmap, norm=hex_norm)

            # Plot hexbin plot
            ax_hexbin.hexbin(oned_vnp, oned_vj1, gridsize=50, cmap=hex_cmap.cmap, norm=hex_norm)
            # Plot the 1:1 line
            ax_hexbin.plot([0, overall_max], [0, overall_max], 'k', linestyle='--')
            # Set axes limits and labels
            ax_hexbin.set_xlim(overall_min, overall_max)
            ax_hexbin.set_ylim(overall_min, overall_max)
            ax_hexbin.set_xlabel(f'VNP{product} {figure_keyword}')
            ax_hexbin.set_ylabel(f'VJ1{product} {figure_keyword}')

            # Set up the axis-mounted histograms
            ax.tick_params(direction='in', top=True, right=True)
            ax_histx = plt.axes(rect_histx)
            ax_histx.tick_params(direction='in', labelbottom=False)
            ax_histx.axis('off')
            ax_histy = plt.axes(rect_histy)
            ax_histy.tick_params(direction='in', labelleft=False)
            ax_histy.axis('off')

            # Plot the histograms
            ax_histx.hist(oned_vnp, bins=np.arange(0, 1, 0.025), rwidth=0.9, color='dimgrey')
            ax_histy.hist(oned_vj1, bins=np.arange(0, 1, 0.025), orientation='horizontal', rwidth=0.9, color='dimgrey')
            # Set axis limits
            ax_histx.set_xlim(ax_hexbin.get_xlim())
            ax_histy.set_ylim(ax_hexbin.get_ylim())

            # Subplot 6: Histogram of differences
            ax = fig.add_subplot(2, 3, 6)
            # Draw the major tick gridlines (zorder controls plotting order)
            grid = ax.grid(which='major', axis='y', zorder=0)
            # Draw the histogram bins (zorder of at least 3 was required to plot in the foreground)
            ax.hist(oned_diff,
                    bins=np.arange(-1, 1, 0.05),
                    weights=np.zeros_like(oned_diff) + 1. / oned_diff.size,
                    color='dimgrey',
                    zorder=3)
            # Set limits and labels
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
