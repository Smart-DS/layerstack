
import setuptools
from pathlib import Path

here = Path(__file__).parent

# Get the long description from the README file
with open(here / 'README.txt', encoding='utf-8') as f:
    long_description = f.read()

with open(here / 'layerstack' / '_version.py', encoding='utf-8') as f:
    version = f.read()

version = version.split()[2].strip('"').strip("'")

setuptools.setup(
    name = 'layerstack',
    version = version,
    author = 'Elaine Hale, Michael Rossol',
    author_email = 'elaine.hale@nrel.gov',
    packages = setuptools.find_packages(),
    python_requires='>=3.6',
    url = 'https://github.com/Smart-DS/layerstack',
    description = 'Python package for assembling, sharing, and running workflows, especially those associated with modifying, running, and analyzing simulation models',
    long_description = long_description,
    package_data = {
        '': ['LICENSE'],
        'layerstack': ['*.template'],
        'layerstack.tests': ['layer_library/*/layer.py',
                             'stack_library/*.json']
    },
    install_requires=[
        'jinja2'
    ],
    extras_require={
        'dev': [
            'ghp-import',
            'numpydoc',
            'pandoc',
            'pytest',
            'pytest-ordering',
            'sphinx',
            'sphinx_rtd_theme',
            'twine'
        ]
    },
    entry_points={
        'console_scripts': [
            'layerstack_stack=layerstack.stack:main'
        ]
    },
    classifiers=[
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
)
