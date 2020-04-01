import pytest

from layerstack.args import ArgMode
from layerstack.layer import Layer
from layerstack.stack import Stack

from tests import here, outdir
from tests.test_session import manage_outdir

layer_library_dir = here / 'layer_library'

stack_library_dir = outdir / 'test_stack_save_load'

@pytest.fixture(scope='module',autouse=True)
def create_layer_library_dir(manage_outdir):
    assert outdir.exists(), outdir
    assert not stack_library_dir.exists()
    stack_library_dir.mkdir()

def test_stack_list_args_layer():
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
