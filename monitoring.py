"""
monitoring.py: Contains functions for monitoring and logging performance
"""

import time
import logging
from datetime import datetime
import os
logger = logging.getLogger("align_logger")


def setup_logger():
    # Loggers
    os.makedirs("logs", exist_ok=True)
    logger.setLevel(logging.DEBUG)
    filename = "logs"+os.sep + datetime.now().strftime('logs_%Y_%m_%d_%H_%M.log')
    file_handler = logging.FileHandler(filename)

    # file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def timeit(f):
    def timed(*args, **kw):
        ts = time.time()
        logger.debug("")
        logger.debug("\t>> Starting timer for %r() <<" % (f.__name__))
        result = f(*args, **kw)
        te = time.time()
        logger.debug("\t>> Time taken for %r() : %.6f sec <<" %
                     (f.__name__, te-ts))
        logger.debug("")

        return result
    return timed
