from __future__ import print_function, division, absolute_import

import os
import subprocess

import pytest

from layerstack.layer import Layer, LayerBase, ModelLayerBase
from tests import outdir
import tests.layer_library

d = os.path.dirname(os.getcwd())
layer_library_dir = os.path.join(d, 'layer_library/test_list_args')

test_list = ['1', '2', '3']

def test_python_layer():
    # should be able to run the layer as-is and 
    out_list = subprocess.check_output(['python',os.path.join(layer_library_dir ,'layer.py'),test_list])
    assert out_list == test_list



