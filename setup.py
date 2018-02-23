
from distutils.core import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, './README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(os.path.join(here, 'layerstack', '_version.py'), encoding='utf-8') as f:
    version = f.read()

version = version.split()[2].strip('"').strip("'")

setup(
    name = 'layerstack',
    version = version,
    author = 'Elaine Hale, Michael Rossol',
    author_email = 'elaine.hale@nrel.gov',
    packages = ['layerstack','tests'],
    url = 'https://github.com/Smart-DS/layerstack',
    description = 'Python package for assembling, sharing, and running workflows, especially those associated with modifying, running, and analyzing simulation models',
    long_description=long_description,
    install_requires=open('requirements.txt').read()
)
