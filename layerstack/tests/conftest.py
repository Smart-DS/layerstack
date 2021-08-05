'''
:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--no-clean-up", action="store_true", default=False, 
        help="Pass this option to leave test outputs in place"
    )

@pytest.fixture(scope="session",autouse=True)
def clean_up(request):
    return (not request.config.getoption('--no-clean-up'))
