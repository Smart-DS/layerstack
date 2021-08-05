'''
[LICENSE]
Copyright (c) 2020 Alliance for Sustainable Energy, LLC, All Rights Reserved

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. The entire corresponding source code of any redistribution, with or without modification, by a research entity, including but not limited to any contracting manager/operator of a United States National Laboratory, any institution of higher learning, and any non-profit organization, must be made publicly available under this license for as long as the redistribution is made available by the research entity.

4. Redistribution of this software, without modification, must refer to the software by the same designation. Redistribution of a modified version of this software (i) may not refer to the modified version by the same designation, or by any confusingly similar designation, and (ii) must refer to the underlying software originally provided by Alliance as "layerstack". Except to comply with the foregoing, the term "layerstack", or any confusingly similar designation may not be used to refer to any modified version of this software or any modified version of the underlying software originally provided by Alliance without the prior written consent of Alliance.

5. The name of the copyright holder(s), any contributors, the United States Government, the United States Department of Energy, or any of their employees may not be used to endorse or promote products derived from this software without specific prior written permission from the respective party.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[/LICENSE]
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
