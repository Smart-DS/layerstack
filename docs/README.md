# Sphinx Documentation

The documentation is built with [Sphinx](http://sphinx-doc.org/index.html). See their documentation for (a lot) more details.

## Installation

To generate the docs yourself, you'll need the appropriate package:

```
pip install sphinx
```

## Refreshing the API Documentation

- Make sure layerstack is in your PYTHONPATH
- Delete the contents of `source/api`.
- Run `sphinx-apidoc -o source/api ..` from the `doc` folder.
- Compare `source/api/modules.rst` to `source/api.rst`.
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
