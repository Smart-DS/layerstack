from __future__ import print_function, division, absolute_import

import os
import subprocess
from subprocess import Popen, PIPE
import shlex
import sys

import pytest

from layerstack.layer import Layer, LayerBase, ModelLayerBase
from tests import outdir
import tests.layer_library

d = os.getcwd()

layer_library_dir = os.path.join(d, 'layer_library/test_list_args')

test_list = ['1', '2', '3']

def test_python_layer():
    args = ['python',os.path.join(layer_library_dir ,'layer.py'), '1', '2', '3']
    out_list = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = out_list.communicate()

    stderr = stderr.decode('ascii').rstrip()
    assert stderr[-15:] == str(test_list)




