'''
:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''
from __future__ import print_function, division, absolute_import

import json
import subprocess
import sys

import pytest

from layerstack import ArgMode, LayerStackRuntimeError
from layerstack.layer import Layer, LayerBase, ModelLayerBase
from layerstack.tests import layer_library_dir, outdir
from layerstack.tests.test_session import manage_outdir

created_layers_library_dir = outdir / 'test_layer_creation'


class ModelForTests(object):
    def __init__(self, name, count=0, data = []):
        self.name = name
        self.count = count
        self.data = data

    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump({'name': self.name, 
                       'count': self.count,
                       'data': self.data}, f, indent=4)

    @classmethod
    def load(cls, filename):
        json_data = json.load(filename)
        return ModelForTests(json_data['name'],
                             count = json_data['count'],
                             data = json_data['data'])


class LayerBaseClassForTestsWithModels(ModelLayerBase):
    @classmethod
    def _check_model_type(cls, model):
        assert isinstance(model, ModelForTests)
    
    @classmethod
    def _load_model(cls, model_path):
        return ModelForTests.load(model_path)

    @classmethod
    def _save_model(cls, model, model_path):
        model.save(model_path)


@pytest.fixture(scope='module',autouse=True)
def create_layer_library_dir(manage_outdir):
    assert outdir.exists(), outdir
    assert not created_layers_library_dir.exists()
    created_layers_library_dir.mkdir()


def test_layer_base():
    _layer_dir = Layer.create('Test Layer Base', created_layers_library_dir)
    # should be able to run the layer as-is
    subprocess.check_call([
        sys.executable, 
        str(created_layers_library_dir / 'test_layer_base' / 'layer.py'), 
        'dummy_arg'])


def test_model_dependent_args_kwargs():
    # without model
    layer = Layer(layer_library_dir / 'test_model_dependent_args_kwargs')
    assert not layer.args[1].is_list, layer.args[1]
    assert layer.kwargs['data_element'].choices is None, layer.kwargs['data_element']
    layer.set_arg_mode(ArgMode.USE)
    layer.args[0] = 'hello'
    layer.args[1] = 1
    layer.kwargs['data_element'] = 'anything allowed'
    assert layer.runnable

    # a model with no data
    model = ModelForTests('Gilbert', count = 2)
    layer = Layer(layer_library_dir / 'test_model_dependent_args_kwargs', model = model)
    assert layer.args[1].is_list, layer.args[1]
    assert layer.args[1].nargs == 2, layer.args[1]
    assert layer.kwargs['data_element'].choices is None, layer.kwargs['data_element']
    layer.set_arg_mode(ArgMode.USE)
    layer.args[0] = model.name
    with pytest.raises(Exception):
        layer.args[1] = 1
    layer.kwargs['data_element'] = 'anything allowed'
    assert not layer.runnable
    layer.args[1] = [3, 4]
    assert layer.runnable

    # a model with data
    model = ModelForTests('Paula', count = 1, data = ['red', 'green', 'purple'])
    layer = Layer(layer_library_dir / 'test_model_dependent_args_kwargs', model = model)
    assert layer.args[1].is_list, layer.args[1]
    assert layer.args[1].nargs == 1, layer.args[1]
    assert len(layer.kwargs['data_element'].choices) == 3, layer.kwargs['data_element']
    assert layer.kwargs['data_element'].default == 'red', layer.kwargs['data_element']
    layer.set_arg_mode(ArgMode.USE)
    layer.args[0] = model.name
    with pytest.raises(Exception):
        layer.args[1] = 1
    assert not layer.runnable
    layer.args[1] = [2]
    assert layer.runnable
    with pytest.raises(LayerStackRuntimeError):
        layer.kwargs['data_element'] = 'anything allowed'
    assert layer.kwargs['data_element'] == 'red', layer.kwargs['data_element']
    layer.kwargs['data_element'] = 'purple'
    assert layer.kwargs['data_element'] == 'purple', layer.kwargs['data_element']
