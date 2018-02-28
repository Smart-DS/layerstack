"""
layerstack is a Python package for assembling workflows, especially those 
associated with modifying, running, and analyzing simulation models
"""

__author__ = """Elaine Hale, Michael Rossol"""
__email__ = 'michael.rossol@nrel.gov'


import hashlib
import logging
import os
from uuid import uuid4

from ._version import __version__


class LayerStackError(Exception):
    """
    Exception base class for this package.
    """
    pass


class LayerStackTypeError(LayerStackError):
    """
    TypeError exception class for this package.
    """
    pass


class LayerStackRuntimeError(LayerStackError):
    """
    RuntimeError exception class for this package.
    """
    pass


FORMAT = '%(asctime)s|%(levelname)s|%(name)s|\n\t%(message)s'


def start_console_log(log_level=logging.WARN,log_format=FORMAT):
    """
    Starts logging to the console.

    Parameters
    ----------
    log_level : enum
        logging package log level, i.e. logging.ERROR, logging.WARN, 
        logging.INFO or logging.DEBUG
    log_format : str
        format string to use with the logging package
    
    Returns
    -------
    logging.StreamHandler
        console_handler
    """
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    logformat = logging.Formatter(log_format)
    console_handler.setFormatter(logformat)
    logging.getLogger().setLevel(log_level)
    logging.getLogger().addHandler(console_handler)
    return console_handler


def start_file_log(filename, log_level=logging.WARN,log_format=FORMAT):
    """
    Starts logging to a file.

    Parameters
    ----------
    filename : str
        path to the log file
    log_level : enum
        logging package log level, i.e. logging.ERROR, logging.WARN, 
        logging.INFO or logging.DEBUG
    log_format : str
        format string to use with the logging package

    Returns
    -------
    logging.FileHandler
        logfile
    """
    logfile = logging.FileHandler(filename=filename)
    logfile.setLevel(log_level)
    logformat = logging.Formatter(log_format)
    logfile.setFormatter(logformat)
    logging.getLogger().setLevel(log_level)
    logging.getLogger().addHandler(logfile)
    return logfile

def checksum(filename):
    """
    Computes the checksum of a file.

    Parameters
    ----------
    filename : str
        file to calculate the checksum for
    :type filename: str

    Returns
    -------
    str
        checksum
    """
    hash_md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

class TempJsonFilepath():
    """
    Creates a temporary json filename. Usage::

        with TempJsonFilepath() as tmpjson:
            # save a json file to tmpjson
            # use the file as needed
            # when this block is exited, the json file will be deleted
            # (used in this package to calculate a json checksum)
    """
    def __init__(self):
        self.filename = str(uuid4()) + '.json'

    def __enter__(self):
        return self.filename

    def __exit__(self, ctx_type, ctx_value, ctx_traceback):
        os.remove(self.filename)

