import t_laads_tools
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
from numpy import around
from os import walk, environ
from dotenv import load_dotenv
from pathlib import Path


# Function for our multi-threaded workers to use
def worker_function(target_url):
    # Start time for the file
    ptime = time()
    # Start a LAADS session (the requests session object is not thread-safe so we need one per thread)
    s = t_laads_tools.connect_to_laads()
    # Get the requested file from the URL
    h5file = t_laads_tools.get_VIIRS_file(s, target_url, write_local=True)
    # Print the time taken
    print(f"{target_url.split('/')[-1]} downloaded in {around(time() - ptime, decimals=2)} seconds.")
    # Return the file
    return h5file


# Function to check whether files have already been downloaded
def check_for_files(url_dict, tiles, dates, url_list=None):
    # If no ongoing url list was provided
    if not url_list:
        # Make an empty list
        url_list = []
    # For each tile
    for tile in tiles:
        # For each date
        for date in dates:
            # Get the file name
            file_name = url_dict.get_url_from_date(tile, date, file_only=True)
            # If the file has not previously been downloaded
            if not check_for_file(file_name):
                # Get the url from date
                target_url = url_dict.get_url_from_date(tile, date)
                # If there was an url
                if target_url:
                    # Add URL to list
                    url_list.append(target_url)
    # Return URL list
    return url_list


# Function to check whether a single file has already been downloaded
def check_for_file(file_name):
    # For each file in the output directory
    for root, dirs, files in walk(Path(environ['output_files_path'])):
        for file in files:
            # If it matches the file name
            if file_name == file:
                # Return True
                return True
    # If we made it this far, file was not found, return False
    return False


# Main function
def main(archive_set, product, tiles, dates):

    # Mark start time
    stime = time()

    # <> We need to spider the products for the archive sets too. This is silly.
    # If the archive set is not 5000 (VNP products only)
    if archive_set != "5000":
        # Retrieve a dictionary of the VJ1 URLs on LAADS
        vj1_dict = t_laads_tools.LaadsUrlsDict(f"VJ1{product}", archive_set=archive_set)
    # If the archive set is not 3194 (VJ1 products only)
    if archive_set != "3194":
        # Retrieve a dictionary of the VNP URLs on LAADS
        vnp_dict = t_laads_tools.LaadsUrlsDict(f"VNP{product}", archive_set=archive_set)

    # Report time elapsed
    print(f"URL dictionary retrieved in {around(time() - stime, decimals=2)} seconds.")
    # Checkpoint the time
    ptime = time()

    # Instantiate URL list
    url_list = []
    # If the archive set is not 5000 (VNP products only)
    if archive_set != "5000":
        # Get list of URLs for VJ1 files that are not already downloaded
        url_list = check_for_files(vj1_dict, tiles, dates, url_list=url_list)
    # If the archive set is not 3194 (VJ1 products only)
    if archive_set != "3194":
        # Update list of URLs for VNP files that are not already downloaded
        url_list = check_for_files(vnp_dict, tiles, dates, url_list=url_list)
    # Report time elapsed
    print(f"List of {len(url_list)} URLs formed in {around(time() - ptime, decimals=2)} seconds.")
    # Checkpoint the time
    ptime = time()

    # Start a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit the tasks from the url list to the worker function
        future_events = {executor.submit(worker_function, target_url): target_url for target_url in
                         url_list}
        # As each worker finishes its work (i.e. as each worker function finishes)
        for completed_event in as_completed(future_events):
            # The completed events are keys for the future_events dictionary
            # Referencing the value for the key returns the inputs that were submitted to the worker (the url in this case)
            original_task = future_events[completed_event]
            # Calling the .result() method returns whatever is returned by the function the workers performed
            # In this case we submitted tasks to the worker_function which returns the h5file object
            h5obj = completed_event.result()

    # Report on the overall time taken
    print(f"All downloads finished in {around(time() - stime, decimals=2)} seconds.")


# If file called directly
if __name__ == "__main__":

    # Load the environmental variables from .env file
    load_dotenv()

    # Archive set for product. Enter as number only (e.g. for AS3397, enter "3397")
    arch_set = "3194"

    # Product base name (e.g. for VNP43MA3 versus VJ143MA3, enter "43MA3")
    product_base = "43MA4"

    # Tile list
    tile_list = ["h09v05", "h12v04", "h17v01"]

    # Date list
    date_list = [datetime.date(year=2021,
                               month=7,
                               day=20)]

    # Run main function
    main(arch_set, product_base, tile_list, date_list)