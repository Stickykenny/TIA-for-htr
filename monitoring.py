"""
monitoring.py: Contains functions for monitoring and logging performance/time
"""

import time
import logging
from datetime import datetime
import os
logger = logging.getLogger("TIA_logger")


def setup_logger():
    """
    Setup the default logger

    Returns :
        The logger
    """

    os.makedirs("logs", exist_ok=True)

    # Set parameters and default values of logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a File Handler to log into a file
    filename = "logs"+os.sep + datetime.now().strftime('logs_%Y_%m_%d_%H_%M.log')
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)

    # Create a Stream Handler for stream's output on console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def timeit(f):
    """
    Decorator used for timing runtime of a function, it logs them using the logger

    Parameters :
        f :
            Function to monitor

    Returns :
        Result of the function
    """
    def timed(*args, **kw):
        # Start the timer
        ts = time.time()

        logger.debug("")
        logger.debug("\t>> Starting timer for %r() <<" % (f.__name__))

        result = f(*args, **kw)  # Apply the function

        # End the timer
        te = time.time()
        logger.debug("\t>> Time taken for %r() : %.6f sec <<" %
                     (f.__name__, te-ts))
        logger.debug("")

        return result
    return timed
