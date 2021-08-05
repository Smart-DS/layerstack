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
import logging
from pathlib import Path
import subprocess
from subprocess import Popen, PIPE
import sys

from layerstack.tests import layer_library_dir, get_output_str

logger = logging.getLogger(__name__)


def test_layer_cli():
    test_list = ['1', '2', '3']

    args = [sys.executable, str(layer_library_dir / 'test_list_args' / 'layer.py')] 
    args += test_list

    out_list = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = out_list.communicate()

    stderr = stderr.decode('ascii').rstrip()
    logger.debug(f"In test_layer_cli, stdout:\n{stdout}\nstderr:\n{stderr}")
    assert stderr[-15:] == str(test_list), f"stdout:\n{stdout}\nstderr:\n{stderr}"


def test_kwarg_name_clashes():
    args = [sys.executable, str(layer_library_dir / 'test_kwarg_name_clashes' / 'layer.py')]

    # run help
    ret = subprocess.run(args + ["--help"], capture_output=True)
    logger.debug(f"In test_kwarg_name_clashes, stdout:\n{get_output_str(ret.stdout)}\n"
        f"stderr:\n{get_output_str(ret.stderr)}\nreturncode = {ret.returncode}\n"
        "after calling --help")
    assert not ret.returncode, get_output_str(ret.stderr)
    
    to_call = [
        "-hr", str(0.2),
        "-hrd", "Rufus",
        "-her", str(85),
        "-herd", "Anne"
    ]

    # run layer
    ret = subprocess.run(args + to_call, capture_output=True)
    logger.debug(f"In test_kwarg_name_clashes, stdout:\n{get_output_str(ret.stdout)}\n"
        f"stderr:\n{get_output_str(ret.stderr)}\nreturncode = {ret.returncode}\n"
        "after calling with kwargs")
    assert not ret.returncode, get_output_str(ret.stderr)


def test_kwargs_with_dashes():
    args = [sys.executable, str(layer_library_dir / 'test_kwargs_with_dashes' / 'layer.py')]

    # run help
    ret = subprocess.run(args + ["--help"], capture_output=True)
    logger.debug(f"In test_kwargs_with_dashes, stdout:\n{get_output_str(ret.stdout)}\n"
        f"stderr:\n{get_output_str(ret.stderr)}\nreturncode = {ret.returncode}\n"
        "after calling --help")
    assert not ret.returncode, get_output_str(ret.stderr)
    
    to_call = [
        "-hr", str(0.2),
        "-hrd", "Rufus",
        "-her", str(85),
        "-herd", "Anne",
        str(734)
    ]

    # run layer
    ret = subprocess.run(args + to_call, capture_output=True)
    logger.debug(f"In test_kwargs_with_dashes, stdout:\n{get_output_str(ret.stdout)}\n"
        f"stderr:\n{get_output_str(ret.stderr)}\nreturncode = {ret.returncode}\n"
        "after calling with kwargs")
    assert not ret.returncode, get_output_str(ret.stderr)
