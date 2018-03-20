# layerstack development instructions

To get all of the development dependencies:

```
pip install -r layerstack/dev/requirements.txt
```

[release process overview](#release-process-overview) | [how to run tests](#how-to-run-tests)

## release process overview

## how to run tests

## documentation

The documentation is built with [Sphinx](http://sphinx-doc.org/index.html). See their documentation for (a lot) more details. To get set-up:

```
pip install sphinx
```

## Refreshing the API Documentation

- Make sure layerstack is in your PYTHONPATH
- Delete the contents of `source/api`.
- Run `sphinx-apidoc -o source/api ..` from the `docs` folder.
- Compare `source/api/modules.rst` to `source/api.rst`.
- 'git push' changes to the documentation source code as needed.
- Make the documentation per below

## Building HTML Docs

### Mac/Linux

```
make html
```

### Windows

```
make.bat html
```

## Building PDF Docs

To build a PDF, you'll need a latex distribution for your system. 

### Mac/Linux

```
make latexpdf
```

### Windows

```
make.bat latexpdf
```

## Pushing to GitHub Pages

### Mac/Linux

```
make github
```

### Windows

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
