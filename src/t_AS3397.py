import h5py
import datetime
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from os import walk, environ
import dotenv
from t_laads_tools import zero_pad_number, get_doy_from_date
from pathlib import Path

# Load environmental variables
dotenv.load_dotenv()

# Set matplotlib defaults for fonts
mpl.rc('font', family='Times New Roman')
mpl.rc('axes', labelsize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

def compare_images(tile, date):

    # Assemble target file name from date
    file_name = f".A{date.year}{get_doy_from_date(date, zero_pad=3)}.{tile}"
    # Instantiate VNP and VJ1 file names
    vnp_filename = None
    vj1_filename = None
    # For all the files in the output path
    for root, dirs, files in walk(Path(environ['output_files_path'])):
        for file in files:
            if "VNP43MA1" + file_name in file:
                vnp_filename = file
            if "VJ143MA1" + file_name in file:
                vj1_filename = file
            # If we've found both file names
            if vnp_filename and vj1_filename:
                # Break the loop
                break
    # If we've found both file names
    # <> Which file is missing?
    if not vnp_filename or not vj1_filename:
        # Print a warning
        print("Warning, one of the expected files was not found.")
        # Exit
        return
    # Open the files
    vnp_file = h5py.File(Path(environ['output_files_path'] + vnp_filename))

    VJ143MA1.A2021001.h09v05.002.2022153232020

    # Check we have both files (VJ1 and VNP)

    # Open as arrays

    # Subtract VJ1 from VNP (ignore empty pixels)

    # Visualize the results (histogram)

    pass

def draw_histogram():

    fig = plt.figure(figsize=(20, 5))
    ax = fig.add_subplot(1, 1, 1)
    daily, = ax.plot(date_list, timeseries_ntl, linewidth=1, label="Daily NTL")
    gapfilled, = ax.plot(date_list, gf_timeseries_ntl, 'r', linewidth=1, label="Daily GF NTL")
    ax.set_xlabel("Date")
    ax.set_ylabel("NTL ")
    ax.set_title(
        f"City: {poly_info.dictionary[poly_id][1]}, {poly_info.dictionary[poly_id][3]}, Polygon {poly_id}, Tile {tile_id}")
    ax.set_ylabel('NTL (nW cm$^-$$^2$ sr$^-$$^1$)')
    ax.legend(handles=[daily, gapfilled], edgecolor='k')
    ax.set_xlim(datetime.datetime(year=2012, month=1, day=1), datetime.datetime.today())

    pass