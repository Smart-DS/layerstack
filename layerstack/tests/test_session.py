'''
layerstack.tests.test_session
-----------------------------
This module contains items that pertain to the entire test session.

:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''

import shutil

import pytest

from layerstack.tests import outdir

STARTUP = True

@pytest.fixture(scope="session",autouse=True)
def manage_outdir(request, clean_up):
    """
    At the beginning of the session, creates the test outdir. If tests.clean_up,
    deletes this folder after the tests have finished running.

    Arguments
    - request contains the pytest session, including collected tests
    """
    global STARTUP
    if STARTUP:
        if outdir.exists():
            # create clean space for running tests
            shutil.rmtree(outdir)
        STARTUP = False
        outdir.mkdir()
    def finalize_outdir():
        if outdir.exists() and clean_up:
            shutil.rmtree(outdir)
    request.addfinalizer(finalize_outdir)
