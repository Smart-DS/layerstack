# layerstack development instructions

To get all of the development dependencies for Python:

```
pip install -r layerstack/dev/requirements.txt
```

Also, you will need to install

- [pandoc](https://pandoc.org/installing.html)

[release process overview](#release-process-overview) | [how to run tests](#how-to-run-tests) | [publish documentation](#publish-documentation) | [release on pypi](#release-on-pypi)

## release process overview

1. Update version number, CHANGES.txt, setup.py, LICENSE and header as needed
2. Run tests locally and fix any issues
3. **Ideally we would** run tests on draft (master branch) package installed from github (`pip install git+https://github.com/Smart-DS/layerstack.git`) and fix any issues, **but tests cannot be installed in a runnable way using current structure**
4. Uninstall the draft package
5. Publish documentation
6. Create release on github
7. Release tagged version on pypi
8. Install released package and re-run tests

## how to run tests

To run tests locally:

```bash
# add layerstack to PYTHONPATH
cd layerstack
pytest
```

To run tests on an installed package:

```
# Still working on this. May need to wait for CI.
```

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

- Make sure layerstack is in your PYTHONPATH
- Delete the contents of `source/api`.
- Run `sphinx-apidoc -o source/api ..` from the `docs` folder.
- Compare `source/api/modules.rst` to `source/api.rst`.
- 'git push' changes to the documentation source code as needed.
- Make the documentation per below

### Building HTML Docs

Run `make html` for Mac and Linux; `make.bat html` for Windows.

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

## release on pypi
