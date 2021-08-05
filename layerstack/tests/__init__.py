# -*- coding: utf-8 -*-

from pathlib import Path

here = Path(__file__).parent
outdir = here / 'outputs'
layer_library_dir = here / 'layer_library'

def get_output_str(stdout_stderr):
    if not isinstance(stdout_stderr, bytes):
        stdout_stderr = stdout_stderr.read() # _io.BufferedReader
    return stdout_stderr.decode("utf-8")
