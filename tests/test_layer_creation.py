from __future__ import print_function, division, absolute_import

import os
import subprocess

import pytest

from layerstack.layer import Layer, LayerBase, ModelLayerBase
from tests import outdir
from tests.test_session import manage_outdir

layer_library_dir = os.path.join(outdir,'test_layer_creation')

@pytest.fixture(scope='module',autouse=True)
def create_layer_library_dir(manage_outdir):
    assert os.path.exists(outdir)
    assert not os.path.exists(layer_library_dir)
    os.mkdir(layer_library_dir)

def test_layer_base():
    layer_dir = Layer.create('Test Layer Base',layer_library_dir)
    # should be able to run the layer as-is
    subprocess.check_call(['python',os.path.join(layer_dir,'layer.py'),'dummy_arg'])
