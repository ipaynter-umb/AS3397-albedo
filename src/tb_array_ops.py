import h5py
from pathlib import Path
from os import environ
import dotenv
import numpy as np
from matplotlib import pyplot as plt

# Load the environmental variables
dotenv.load_dotenv()

# Open the vnp and vj1 files as h5py File objects
vnp_file = h5py.File(Path(environ['output_files_path'] + 'VJ143MA3.A2021001.h09v05.002.2022153232020.h5'))
#vj1_file = h5py.File(Path(environ['output_files_path'] + 'VJ143MA1.A2021004.h09v05.002.2022154021510.h5'))

for key in vnp_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'].keys():
    print(key)
    continue
    if "Quality" in key:
        qual_array = np.array(vnp_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields'][key])
        oned_qual = np.reshape(qual_array, qual_array.shape[0] * qual_array.shape[1])
        print(np.nanmax(np.where(oned_qual != 255, oned_qual, np.nan)))
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.hist(oned_qual, bins=np.arange(0, 10, 1))

        plt.show()

exit()

# Get the array for a specific band
vnp_array = np.array(vnp_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields']['BRDF_Albedo_Parameters_M1'])
vj1_array = np.array(vj1_file['HDFEOS']['GRIDS']['VIIRS_Grid_BRDF']['Data Fields']['BRDF_Albedo_Parameters_M1'])

# Swap the fill values (32767 for signed 16 bit integer) for numpy NaN values
vnp_filter_array = np.where(vnp_array[:, :, 0] != 32767, vnp_array[:, :, 0], np.nan)
vj1_filter_array = np.where(vj1_array[:, :, 0] != 32767, vj1_array[:, :, 0], np.nan)

# Print the max (ignoring NaNs)
print(np.nanmax(vnp_filter_array))
print(np.nanmax(vj1_filter_array))

# Subtract the VJ1 band values from the SNPP values
diff_array = np.subtract(vnp_filter_array, vj1_filter_array)

# Calculate the percent difference (relative to VNP)
perc_diff = np.multiply(np.divide(diff_array, vnp_filter_array), 100)

# Transform the difference to a 1D array
oned_diff = np.reshape(perc_diff, perc_diff.shape[0] * perc_diff.shape[1])

# Plot the data
fig = plt.figure(figsize=(8, 5))
ax = fig.add_subplot(1, 1, 1)
ax.imshow(perc_diff)
#fig.colorbar(perc_diff)
plt.show()

# Plot a histogram of the differences
fig = plt.figure(figsize=(8, 5))
ax = fig.add_subplot(1, 1, 1)
ax.hist(oned_diff, bins=20)
ax.set_xlim(np.nanmin(oned_diff), np.nanmax(oned_diff))
plt.show()
