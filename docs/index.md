# MkApi Documentation

MkApi plugin for [MkDocs](https://www.mkdocs.org/) generates API documentation for Python code. MkApi supports two styles of docstrings: [Google](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) and [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard). The [Napoleon package](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html#) provides complete examples:

* [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google)
* [Example NumPy Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy)

Features of MkApi are:

* **Section syntax**: Supported section identifiers are `Args`, `Arguments`, `Attributes`, `Example[s]`, `Note[s]`, `Parameters`, `Raises`, `Returns`, `References`, `Todo`, `Warning[s]`, `Warns`, and `Yields`.
* **Type annotation**: If you write your function such as `def func(x: int) -> str:`, you don't need write type(s) in Parameters, Returns, or Yields section again. You can overwrite the type annotation in the corresponding docstring.
* **Object type inspection**: MkApi plugin creates CLASS, DATACLASS, FUNCTION, GENERATOR, or METHOD prefix for each object.
* **Attribute inspection**: If you write attributes with description as comment at module level or in `__init__()` of class, Attributes section is automatically created.
* **Docstring inheritance**: Docstring of a subclass can inherit parameters and attributes description from its superclasses.
* **Page mode**: Comprehensive API documentation for your project, in which objects are linked to each other by type annotation.


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
![mkapi](<object.full.name>)
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

* [Google style examples](examples/google_style.md)
* [NumPy style examples](examples/numpy_style.md)

### Page Mode

Using the page mode, you can construct a comprehensive API documentation for your project. You can get this powerful feature by just one line:

~~~yaml
nav:
  - index.md
  - API: mkapi/api/mkapi
~~~

For more details, see [Page Mode and Internal Links](usage/page.md)
