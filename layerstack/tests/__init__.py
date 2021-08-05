# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path

here = Path(__file__).parent
outdir = here / 'outputs'
layer_library_dir = here / 'layer_library'

def get_output_str(stdout_stderr):
    if not isinstance(stdout_stderr, bytes):
        stdout_stderr = stdout_stderr.read() # _io.BufferedReader
    return stdout_stderr.decode('ascii').rstrip()

def run_command(args, logger, test_name, msg_postfix):
    ret = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = ret.communicate()
    stdout = get_output_str(stdout); stderr = get_output_str(stderr)
    logger.debug(f"In {test_name}, stdout:\n{stdout}\nstderr:\n{stderr}\n"
        f"returncode = {ret.returncode}\n{msg_postfix}")
    return ret, stdout, stderr