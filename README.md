[![PyPI version][pypi-image]][pypi-link]
[![Python versions][pyversions-image]][pyversions-link]
[![Travis][travis-image]][travis-link]
[![AppVeyor][appveyor-image]][appveyor-link]
[![Coverage Status][coveralls-image]][coveralls-link]
[![Code style: black][black-image]][black-link]

# MkApi

MkApi plugin for [MkDocs](https://www.mkdocs.org/) generates API documentation for Python code. MkApi (partially) supports two styles of docstrings: [Google](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) and [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard). [Napoleon package](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html#) provides complete examples:

* [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google)
* [Example NumPy Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy)

Features of MkApi are:

* Section syntax. Supported sections are `Args`, `Arguments`, `Attributes`, `Example[s]`, `Note[s]`, `Parameters`, `Raises`, `Returns`, `References`, `Todo`, `Warning[s]`, `Warns`, and `Yields`.
* Type annotation. If you write your function such as `def func(x: int) -> str:`, you don't need write type(s) in `Args`, `Parameters`, `Returns`, or `Yields` section again. You can overwrite the type annotation in the corresponding docstring.
* Object type inspection. MkApi plugin creates `CLASS`, `DATACLASS`, `FUNCTION`, `GENERATOR`, `METHOD`, or `PROPERTY` prefix for each object.

## Installation

Install the plugin using pip:

~~~bash
pip install mkapi
~~~

## Configuration

Add the following lines to `mkdocs.yml`:

~~~yml
plugins:
  - search # necessary for search to work
  - mkapi
~~~

## Usage

To generate the API documentation, add an exclamation mark (!), followed by `mkapi` in brackets, and the object qualname in parentheses. Yes, this is like adding an image. The object can be a package, module, function, class, *etc*.

~~~markdown
![mkapi](<object.qualname>)
~~~

The MkApi plugin imports objects that you specify. If they aren't in the `sys.path`, configure `mkdocs.yml` like below:

~~~yml
plugins:
  - search
  - mkapi:
      src_dirs: [<path_1>, <path_2>, ...]
~~~

Here, `path_X`s are inserted to `sys.path`. These `path_X`s are relative paths to the directory in which `mkdocs.yml` exists.


## MkApi Documentation

For more details see [MkApi Documentation](https://mkapi.daizutabi.net)


[pypi-image]: https://badge.fury.io/py/mkapi.svg
[pypi-link]: https://pypi.org/project/mkapi
[travis-image]: https://travis-ci.org/daizutabi/mkapi.svg?branch=master
[travis-link]: https://travis-ci.org/daizutabi/mkapi
[appveyor-image]: https://ci.appveyor.com/api/projects/status/ys2ic8n4j7r5j4bg/branch/master?svg=true
[appveyor-link]: https://ci.appveyor.com/project/daizutabi/mkapi
[coveralls-image]: https://coveralls.io/repos/github/daizutabi/mkapi/badge.svg?branch=master
[coveralls-link]: https://coveralls.io/github/daizutabi/mkapi?branch=master
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/ambv/black
[pyversions-image]: https://img.shields.io/pypi/pyversions/mkapi.svg
[pyversions-link]: https://pypi.org/project/mkapi
