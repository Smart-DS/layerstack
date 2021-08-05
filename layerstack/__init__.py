"""
layerstack
----------
layerstack is a Python package for assembling workflows, especially those 
associated with modifying, running, and analyzing simulation models

:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
"""

__author__ = """Elaine Hale, Michael Rossol"""
__email__ = 'michael.rossol@nrel.gov'


import hashlib
import logging
from os import remove
import sys
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


DEFAULT_LOG_FORMAT = '%(asctime)s|%(levelname)s|%(name)s|\n\t%(message)s'


def start_console_log(log_level=logging.WARN,log_format=DEFAULT_LOG_FORMAT):
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


def start_file_log(filename, log_level=logging.WARN,log_format=DEFAULT_LOG_FORMAT):
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


def end_file_log(logfile):
    logfile.close()
    logging.getLogger().removeHandler(logfile)


def checksum(filename):
    """
    Computes the checksum of a file.

    Parameters
    ----------
    filename : str
        file to calculate the checksum for

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
        remove(self.filename)


def load_module_from_file(module_name, module_path):
    """
    Loads a python module from the path of the corresponding file. (Adapted 
    from https://github.com/epfl-scitas/spack/blob/af6a3556c4c861148b8e1adc2637685932f4b08a/lib/spack/llnl/util/lang.py#L595-L622)

    Parameters
    ----------
    module_name : str
        namespace where the python module will be loaded
    module_path : str
        path of the python file containing the module
    
    Returns
    -------
    module
        A valid module object
    
    Raises
    ------    
    ImportError 
        when the module can't be loaded
    FileNotFoundError
        when module_path doesn't exist
    """
    if sys.version_info[0] == 3 and sys.version_info[1] >= 5:
        # Python 3, 3.5 or less
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif sys.version_info[0] == 3 and sys.version_info[1] < 5:
        # Python 3, 3.6 or higher
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader(module_name, module_path)
        module = loader.load_module()
    elif sys.version_info[0] == 2:
        # Python 2
        import imp
        module = imp.load_source(module_name, module_path)

    return module


def timer_str(elapsed_seconds):
    result = ''; sep = ''
    days, remainder = divmod(elapsed_seconds, 60*60*24)
    if days:
        result += sep + f'{days:0.0f} d'; sep = ' '
    hours, remainder = divmod(remainder, 60*60)
    if hours: 
        result += sep + f'{hours:0.0f} h'; sep = ' '
    minutes, remainder = divmod(remainder, 60)
    if minutes:
        result += sep + f'{minutes:0.0f} m'; sep = ' '
    if days or hours:
        result += sep + f'{remainder:0.0f} s'
    elif minutes:
        result += sep + f'{remainder:0.1f} s'
    else:
        result += sep + f'{remainder} s'
    return result


# import objects required for basic use so they can be imported directly 
# from layerstack
from .args import ArgMode
from .layer import Layer
from .stack import Stack