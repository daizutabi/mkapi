[![PyPI version][pypi-image]][pypi-link]
[![Python versions][pyversions-image]][pyversions-link]
[![Travis][travis-image]][travis-link]
[![AppVeyor][appveyor-image]][appveyor-link]
[![Coverage Status][coveralls-image]][coveralls-link]
[![Code style: black][black-image]][black-link]

# MkApi

MkApi plugin for [MkDocs](https://www.mkdocs.org/) generates API documentation for Python code. MkApi supports two styles of docstrings: [Google](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) and [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).

Features of MkApi are:

* **Type annotation**: If you write your function such as `def func(x: int) -> str:`, you don't need write type(s) in Parameters, Returns, or Yields section again. You can overwrite the type annotation in the corresponding docstring.
* **Object type inspection**: MkApi plugin creates *class*, *dataclass*, *function*, or *generator* prefix for each object.
* **Attribute inspection**: If you write attributes with description as comment in module or class, Attributes section is automatically created.
* **Docstring inheritance**: Docstring of a subclass can inherit parameters and attributes description from its superclasses.
* **Table of Contents**: Table of contents are inserted into the documentation of each package, module, and class.
* **Page mode**: Comprehensive API documentation for your project, in which objects are linked to each other by type annotation.
* **Bidirectional Link**: Using the Page mode, bidirectional links are created between documentation and source code.

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

MkApi provides two modes to generate API documentation: Embedding mode and Page mode.

### Embedding Mode

To generate the API documentation in a Markdown source, add an exclamation mark (!), followed by `mkapi` in brackets, and the object full name in parentheses. Yes, this is like adding an image. The object can be a function, class, or module.

~~~markdown
![mkapi](<package.module.object>)
~~~

You can combine this syntax with Markdown heading:

~~~markdown
## ![mkapi](<package.module.object>)
~~~

MkApi imports objects that you specify. If they aren't in the `sys.path`, configure `mkdocs.yml` like below:

~~~yml
plugins:
  - search
  - mkapi:
      src_dirs: [<path1>, <path2>, ...]
~~~

Here, `pathX`s are inserted to `sys.path`. These `pathX`s must be relative to the `mkdocs.yml` directory.

The embedding mode is useful to embed an object interface in an arbitrary position of a Markdown source. For more details, see:

* [Google style examples](https://mkapi.daizutabi.net/examples/google_style)
* [NumPy style examples](https://mkapi.daizutabi.net/examples/numpy_style)

### Page Mode

Using the page mode, you can construct a comprehensive API documentation for your project. You can get this powerful feature by just one line:

~~~yaml
nav:
  - index.md
  - API: mkapi/api/mkapi
~~~

For more details, see [Page Mode and Internal Links](https://mkapi.daizutabi.net/usage/page)

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
