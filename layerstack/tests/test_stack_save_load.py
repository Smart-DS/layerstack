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

from layerstack import ArgMode, Layer, LayerStackError, Stack
from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack

from layerstack.tests import layer_library_dir, outdir
from layerstack.tests.test_session import manage_outdir


def test_stack_list_args_layer():
    stack_library_dir = outdir / 'test_stack_save_load'
    if not stack_library_dir.exists():
        stack_library_dir.mkdir()

    layer = Layer(layer_library_dir / 'test_list_args')
    stack = Stack(layers = [layer], name = 'Test List Args Layer')

    p = stack_library_dir / 'test_stack_list_args_layer_1.json'
    stack.save(p)
    stack = Stack.load(p)

    stack.layers[0].args.mode = ArgMode.USE
    stack.layers[0].args[0] = ['a', 'b']

    p = stack_library_dir / 'test_stack_list_args_layer_2.json'
    stack.save(p)
    stack = Stack.load(p)

    stack.layers[0].args.mode = ArgMode.USE
    assert (stack.layers[0].args[0] == ['a', 'b']), stack.layers[0]


def test_stack_library_dirs():
    stack_library_dir = outdir / 'test_stack_library_dirs'
    if not stack_library_dir.exists():
        stack_library_dir.mkdir()
    
    layer = Layer(layer_library_dir / 'test_list_args')
    stack = Stack(layers = [layer], name = 'Test Layer Library Dirs Load')
    p = stack_library_dir / 'test_stack_library_dirs_1'
    stack.save(p)

    # create alternate location
    alt_layer_library_dir = outdir / 'test_stack_library_dirs'
    orig_layer_dir = layer_library_dir / 'test_list_args' 
    new_layer_dir = alt_layer_library_dir / 'test_list_args'
    shutil.copytree(orig_layer_dir, new_layer_dir)

    stack = Stack.load(
        p, 
        layer_library_dir=alt_layer_library_dir, 
        original_locations_preferred=True)
    stack[0].layer_dir == orig_layer_dir

    stack = Stack.load(
        p, 
        layer_library_dir=alt_layer_library_dir, 
        original_locations_preferred=False)
    stack[0].layer_dir == new_layer_dir
    p = stack_library_dir / 'test_stack_library_dirs_2'
    stack.save(p)

    shutil.rmtree(new_layer_dir)

    with pytest.raises(LayerStackError) as excinfo:
        Stack.load(p)

    assert "Unable to find the layer test_list_args" in str(excinfo.value), str(excinfo.value)
