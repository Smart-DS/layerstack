'''
[LICENSE]
Copyright (c) 2019 Alliance for Sustainable Energy, LLC, All Rights Reserved

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. The entire corresponding source code of any redistribution, with or without modification, by a research entity, including but not limited to any contracting manager/operator of a United States National Laboratory, any institution of higher learning, and any non-profit organization, must be made publicly available under this license for as long as the redistribution is made available by the research entity.

4. Redistribution of this software, without modification, must refer to the software by the same designation. Redistribution of a modified version of this software (i) may not refer to the modified version by the same designation, or by any confusingly similar designation, and (ii) must refer to the underlying software originally provided by Alliance as "layerstack". Except to comply with the foregoing, the term "layerstack", or any confusingly similar designation may not be used to refer to any modified version of this software or any modified version of the underlying software originally provided by Alliance without the prior written consent of Alliance.

5. The name of the copyright holder(s), any contributors, the United States Government, the United States Department of Energy, or any of their employees may not be used to endorse or promote products derived from this software without specific prior written permission from the respective party.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[/LICENSE]
'''
"""
layerstack is a Python package for assembling workflows, especially those 
associated with modifying, running, and analyzing simulation models
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
                