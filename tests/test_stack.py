
import pytest

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
