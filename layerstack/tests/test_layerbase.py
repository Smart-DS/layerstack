'''
:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''
import logging
from pathlib import Path
import sys

from layerstack.tests import layer_library_dir, run_command

logger = logging.getLogger(__name__)


def test_layer_cli():
    test_list = ['1', '2', '3']

    args = [sys.executable, str(layer_library_dir / 'test_list_args' / 'layer.py')] 
    args += test_list

    ret, stdout, stderr = run_command(args, logger, "test_layer_cli", "")
    assert stderr[-15:] == str(test_list), f"stdout:\n{stdout}\nstderr:\n{stderr}"

def test_kwarg_name_clashes():
    args = [sys.executable, str(layer_library_dir / 'test_kwarg_name_clashes' / 'layer.py')]

    # run help
    ret, stdout, stderr = run_command(args + ["--help"], logger, 
        "test_kwarg_name_clashes", "after calling --help")
    assert not ret.returncode, stderr
    
    to_call = [
        "-hr", str(0.2),
        "-hrd", "Rufus",
        "-her", str(85),
        "-herd", "Anne"
    ]

    # run layer
    ret, stdout, stderr = run_command(args + to_call, logger, 
        "test_kwarg_name_clashes", "after calling with kwargs")
    assert not ret.returncode, ret.stderr

def test_kwargs_with_dashes():
    args = [sys.executable, str(layer_library_dir / 'test_kwargs_with_dashes' / 'layer.py')]

    # run help
    ret, stdout, stderr = run_command(args + ["--help"], logger, 
            "test_kwargs_with_dashes", "after calling --help")
    assert not ret.returncode, ret.stderr
    
    to_call = [
        "-hr", str(0.2),
        "-hrd", "Rufus",
        "-her", str(85),
        "-herd", "Anne",
        str(734)
    ]

    # run layer
    ret, stdout, stderr = run_command(args + to_call, logger, 
            "test_kwargs_with_dashes", "after calling with kwargs")
    assert not ret.returncode, ret.stderr
