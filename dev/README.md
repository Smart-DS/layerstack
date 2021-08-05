# layerstack development instructions

To get all of the development dependencies for Python:

```
pip install -r layerstack/dev/requirements.txt
```

Also, you will need to install

- [pandoc](https://pandoc.org/installing.html)

[repository conventions](#repository-conventions) | [release process overview](#release-process-overview) | [how to run tests](#how-to-run-tests) | [publish documentation](#publish-documentation) | [create release](#create-release) | [release on pypi](#release-on-pypi)

## repository conventions

- Documentation is made using Sphinx, and follows NumPy docstring style conventions, please see [Example NumPy Style Python Docstrings on Sphinx site](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html). The NumPy docstrings are interpreted by [Napolean](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/), which relies on sphinx.ext.autodoc. Some helpful tips for how to link to things in Sphinx are available [here](https://kevin.burke.dev/kevin/sphinx-interlinks/). The list of Python object types that can be cross-referenced is available [here](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html?highlight=info%20field%20lists#info-field-lists).

## release process overview

1. Update version number, CHANGES.txt, setup.py, LICENSE and header as needed
2. [Run tests](#how-to-run-tests) locally and fix any issues
3. Push to github and ensure checks pass there
4. Install the package from github (`pip install git+https://github.com/Smart-DS/layerstack.git`), run tests (`pytest --pyargs layerstack`) and fix any remaining issues
5. Uninstall the draft package
6. [Publish documentation](#publish-documentation)
7. [Create release](#create-release) on github
8. [Release tagged version on pypi](#release-on-pypi)
9. Install released package and re-run tests
10. Checkout master branch

## how to run tests

To run tests locally:

```bash
# add layerstack to PYTHONPATH
cd layerstack
pytest
```

To run tests on an installed package:

```
pytest --pyargs layerstack
```

pytest options that may be helpful:

option flag | effect
----------- | ------
--no-clean-up | leaves the `layerstack/tests/outputs` file in place so the items made by tests can be visually inspected
--log-cli-level=DEBUG | emits log messages to the console. level can be set to DEBUG, INFO, WARN, ERROR

## publish documentation

The documentation is built with [Sphinx](http://sphinx-doc.org/index.html). There are several steps to creating and publishing the documentation:

1. Convert .md input files to .rst
2. Refresh API documentation
3. Build the HTML docs
4. Push to GitHub

### Markdown to reStructuredText

Markdown files are registered in `docs/source/md_files.txt`. Paths in that file should be relative to the docs folder and should exclude the file extension. For every file listed there, the `dev/md_to_rst.py` utility will expect to find a markdown (`.md`) file, and will look for an optional `.postfix` file, which is expected to contain `.rst` code to be appended to the `.rst` file created by converting the input `.md` file. Thus, running `dev/md_to_rst.py` on the `docs/source/md_files.txt` file will create revised `.rst` files, one for each entry listed in the registry. In summary:

```
cd docs/source
python ../../dev/md_to_rst.py md_files.txt
```

### Refresh API Documentation

The API documentation is actually made when the HTML docs are built. This step just establishes the package structure, and so only needs to be done if the package structure changes.

- Make sure layerstack is in your PYTHONPATH
- Delete `source/api`.
- Run `sphinx-apidoc -o source/api ../layerstack` from the `docs` folder.
- Compare `source/api/modules.rst` to `source/api.rst`.
- 'git push' changes to the documentation source code as needed.
- Make the documentation per below

### Building HTML Docs

Run `make html` for Mac and Linux; `make.bat html` for Windows. **layerstack** must be in your `PYTHONPATH` during this step for the API documentation to generate correctly.

### Pushing to GitHub Pages

#### Mac/Linux

```
make github
```

#### Windows

```
make.bat html
```

Then run the github-related commands by hand:

```
git branch -D gh-pages
git push origin --delete gh-pages
ghp-import -n -b gh-pages -m "Update documentation" ./build/html
git checkout gh-pages
git push origin gh-pages
git checkout master # or whatever branch you were on
```

## create release

- Go to the [releases](https://github.com/Smart-DS/layerstack/releases) page
- Click on the `Draft a new release` button
- Follow these conventions:
  - Name the tag following the convention `v0.3.1`, where the number after the 'v' matches the version number listed in `layerstack/_version.py`. The middle number is incremented when a new feature is added. The last number is incremented when a bug is fixed (only). The first number is only incremented when a major refactor changes the user interface.
  - The name of the release follows the convention `Version 0.3.1`, where again the listed version number matches what's in `layerstack/_version.py`
  - At a minimum the release description should replicate the list of items that was added to CHANGES.txt

## release on pypi

1. [using testpyi](https://packaging.python.org/guides/using-testpypi/) has good instructions for setting up your user account on TestPyPI and PyPI, and configuring twine to know how to access both repositories.
   
2. Test the package

    ```
    git checkout vX.X.X
    python setup.py sdist
    twine upload --repository testpypi dist/layerstack-X.X.X.tar.gz
    # look at https://test.pypi.org/project/layerstack/
    pip install --index-url https://test.pypi.org/simple/ layerstack
    # check it out ... fix things ...
    ```

3. Upload to pypi

    ```
    twine upload --repository pypi dist/layerstack-X.X.X.tar.gz
    git checkout master
    ```
