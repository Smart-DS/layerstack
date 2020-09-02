
import pytest
import shutil

from layerstack import ArgMode, LayerStackError, Layer, Stack
from tests import layer_library_dir, outdir


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
