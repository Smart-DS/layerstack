'''
:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''

import pytest
import shutil
from pathlib import Path
import logging
from layerstack import ArgMode, LayerStackError, Layer, Stack
from layerstack.tests import layer_library_dir, outdir
from layerstack.stack import repoint_stack, parse_args_helper

import subprocess
from subprocess import Popen, PIPE

logger = logging.getLogger(__name__)


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

# *** create new stack and test repointing ***
def test_repointing_run_dir():
    
    stack_library_dir = outdir / 'test_stack_repoint'
    if not stack_library_dir.exists():
        stack_library_dir.mkdir()

    layer = Layer(layer_library_dir / 'test_list_args')
    stack = Stack(layers = [layer], 
                  name='Basic Test', 
                  run_dir = outdir / 'test_basic_repoint')
    
    p = stack_library_dir / 'test_stack_repoint_layer_1.json'
    stack.save(p)

    assert stack.run_dir is not None

    new_run_dir = outdir / 'new_run_dir'

    repoint_stack(p, run_dir = new_run_dir)

    np = stack_library_dir / '_test_stack_repoint_layer_1.json'
    check_stack = Stack.load(np)
    assert str(check_stack.run_dir) == str(new_run_dir) 


def test_parser():
    cli_arg_list = ['test_hw_amc_5min_simple.json', 'run', '-sp', str(outdir)]
    args = parse_args_helper(cli_arg_list)

    assert args.stack_file == 'test_hw_amc_5min_simple.json'
    assert args.mode == 'run'
    assert args.save_path == str(outdir)
    assert args.layer_library_dirs == None
    assert args.original_locations_preferred == True
    assert args.debug == False
    assert args.warning_only == False
    assert args.archive == True






