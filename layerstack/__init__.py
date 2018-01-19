"""
The ditto.layers subpackage defines the framework needed to
programmatically define and run ditto.Model workflows.
"""
__author__ = """Elaine Hale, Michael Rossol"""
__email__ = 'michael.rossol@nrel.gov'

class LayerStackError(Exception): pass

def start_console_log(log_level=logging.WARN, 
        log_format='%(asctime)s|%(levelname)s|%(name)s|\n    %(message)s'):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    logformat = logging.Formatter(log_format)
    console_handler.setFormatter(logformat)
    logging.getLogger().setLevel(log_level)
    logging.getLogger().addHandler(console_handler)

def start_file_log(filename, log_level=logging.WARN,
        log_format='%(asctime)s|%(levelname)s|%(name)s|\n    %(message)s'):
    logfile = logging.FileHandler(filename=filename)
    logfile.setLevel(log_level)
    logformat = logging.Formatter(log_format)
    logfile.setFormatter(logformat)
    logging.getLogger().setLevel(log_level)
    logging.getLogger().addHandler(logfile)
