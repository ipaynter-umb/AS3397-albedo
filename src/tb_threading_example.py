from concurrent.futures import ThreadPoolExecutor, as_completed
from random import random
from time import sleep

# Function to wait up to 3 seconds then multiply the task number by 2
def wait_and_multiply(number):
    # Declare the task is in progress
    print(f"Task {number} is in progress")
    # Wait up to 3 seconds
    sleep(random() * 3)
    # Return the task number multiplied by 2
    return number * 2

# Make a list of numbers from 0-9
tasks = list(range(0, 10))

# Start a Thread Pool Executor with a specified number of workers
# "with" is used to ensure the threads are cleaned up properly by Python
with ThreadPoolExecutor(max_workers=3) as executor:
    # Submit each number from the tasks list to the executor
    future_events = {executor.submit(wait_and_multiply, number): number for number in
                     tasks}
    # As each worker finishes its work
    for completed_event in as_completed(future_events):
        # The completed events are keys for the future_events dictionary
        # Referencing the value for the key returns the inputs to the worker (i.e. the task number)
        original_task = future_events[completed_event]
        # Calling the .result() method returns whatever is returned by the function the tasks were submitted to
        # In this case we submitted tasks to the "wait_and_multiply" function, which returns the task number doubled
        task_result = completed_event.result()
        print(f"Task {original_task} is finished. Result of task: {task_result}.")