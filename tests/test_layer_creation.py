from __future__ import print_function, division, absolute_import

import os
import subprocess

import pytest

from layerstack.layer import Layer, LayerBase, ModelLayerBase
from tests import ditto_dir, outdir
from tests.test_session import manage_outdir

layer_library_dir = os.path.join(outdir,'test_layer_creation')
gridlabd_models_dir = os.path.join(ditto_dir,'readers','gridlabd')

@pytest.fixture(scope='module',autouse=True)
def create_layer_library_dir(manage_outdir):
    assert os.path.exists(outdir)
    assert not os.path.exists(layer_library_dir)
    os.mkdir(layer_library_dir)

def test_layer_base():
    layer_dir = Layer.create('Test Layer Base',layer_library_dir)
    # should be able to run the layer as-is
    subprocess.check_call(['python',os.path.join(layer_dir,'layer.py'),'dummy_arg'])

class TestModelLayerBase(ModelLayerBase): pass

def test_model_layer():
    layer_dir = Layer.create('Test Model Layer Base',layer_library_dir,layer_base_class=TestModelLayerBase)
    # HERE -- Fix this call
    subprocess.check_call(['python',
                           os.path.join(layer_dir,'layer.py'),
                           os.path.join(gridlabd_models_dir,'4node.glm'),
                           'dummy_arg'])
