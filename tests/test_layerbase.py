import logging
from pathlib import Path
import subprocess
from subprocess import Popen, PIPE
import sys

from tests import layer_library_dir

logger = logging.getLogger(__name__)


def test_layer_cli():
    test_list = ['1', '2', '3']

    args = ['python', str(layer_library_dir / 'test_list_args' / 'layer.py')] 
    args += test_list

    out_list = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = out_list.communicate()

    stderr = stderr.decode('ascii').rstrip()
    logger.debug(f"In test_layer_cli, stdout:\n{stdout}\nstderr:\n{stderr}")
    assert stderr[-15:] == str(test_list), f"stdout:\n{stdout}\nstderr:\n{stderr}"

