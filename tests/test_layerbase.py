from __future__ import print_function, division, absolute_import

from pathlib import Path
import subprocess
from subprocess import Popen, PIPE
import shlex
import sys

import pytest

from tests import layer_library_dir


def test_python_layer():
    test_list = ['1', '2', '3']

    args = ['python', str(layer_library_dir / 'test_list_args' / 'layer.py')] 
    args += test_list

    out_list = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = out_list.communicate()

    stderr = stderr.decode('ascii').rstrip()
    assert stderr[-15:] == str(test_list), f"stdout:\n{stdout}\nstderr:\n{stderr}"

