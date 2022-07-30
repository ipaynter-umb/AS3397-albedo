import t_laads_tools
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
from numpy import around


# Function for our multi-threaded workers to use
def worker_function(target_url):
    # Start time for the file
    ptime = time()
    # Start a LAADS session (the requests session object is not thread-safe so we need one per thread
    s = t_laads_tools.connect_to_laads()
    # Get the requested file from the URL
    h5file = t_laads_tools.get_VIIRS_file(s, target_url, write_local=True)
    # Print the time taken
    print(f"{target_url.split('/')[-1]} downloaded in {around(time() - ptime, decimals=2)} seconds.")
    # Return the file
    return h5file


# Mark start time
stime = time()

# Retrieve a dictionary of the URLs on LAADS
test_dict = t_laads_tools.LaadsUrlsDict("VJ143MA3", archive_set="3397")

# Report time elapsed
print(f"URL dictionary retrieved in {around(time() - stime, decimals=2)} seconds.")
# Checkpoint the time
ptime = time()

# For a list of urls within a specified date range
url_list = test_dict.get_urls_from_date_range(tile="h09v05",
                                              start_date=datetime.date(year=2021, month=1, day=1),
                                              end_date=datetime.date(year=2021, month=1, day=7))

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