import pytest
import shutil

from layerstack import ArgMode, Layer, LayerStackError, Stack
from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack

from tests import layer_library_dir, outdir
from tests.test_session import manage_outdir


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
