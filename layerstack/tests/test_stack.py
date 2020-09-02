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

import pytest
import shutil

from layerstack import ArgMode, LayerStackError, Layer, Stack
from layerstack.tests import layer_library_dir, outdir


def test_layer_types():
    layer = Layer(layer_library_dir / 'test_list_args')
    with pytest.raises(LayerStackError) as excinfo:
        Stack(layers = [layer, 1])

    assert 'int' in str(excinfo.value), str(excinfo.value)

    with pytest.raises(LayerStackError):
        Stack(layers = [layer.layer_dir])


def test_basic_compose_and_run():
    layer = Layer(layer_library_dir / 'test_list_args')
    stack = Stack(layers = [layer], 
                  name='Basic Test', 
                  run_dir = outdir / 'test_basic_compose_and_run')
    stack.set_arg_mode(ArgMode.USE)
    stack[0].args[0] = [1, 2, 3]
    stack.run()


def test_get_layer_dir():
    alt_layer_library_dir = outdir / 'test_get_layer_dir'
    alt_layer_library_dir.mkdir()

    orig_layer_dir = layer_library_dir / 'test_list_args' 
    new_layer_dir = alt_layer_library_dir / 'test_list_args'
    shutil.copytree(orig_layer_dir, new_layer_dir)

    test_layer_dir = Stack.get_layer_dir(
        orig_layer_dir, 
        layer_library_dirs=[alt_layer_library_dir], 
        original_preferred=True)
    assert test_layer_dir == orig_layer_dir

    test_layer_dir = Stack.get_layer_dir(
        orig_layer_dir, 
        layer_library_dirs=[alt_layer_library_dir], 
        original_preferred=False)
    assert test_layer_dir == new_layer_dir

    fake_layer_dir = layer_library_dir / 'my_nonexistent_layer'
    test_layer_dir = Stack.get_layer_dir(
        fake_layer_dir, 
        layer_library_dirs=[alt_layer_library_dir], 
        original_preferred=True)
    assert test_layer_dir is None
