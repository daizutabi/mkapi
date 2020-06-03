# MkApi Documentation

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

MkApi provides two modes to generate API documentation: Embedding mode and Page mode.

### Embedding Mode

To generate the API documentation in a Markdown source, add an exclamation mark (!), followed by `mkapi` in brackets, and the object qualname in parentheses. Yes, this is like adding an image. The object can be a package, module, function, class, *etc*.

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

The embedding mode is useful to embed object interface in a arbitrary position of a Markdown source.

### Page Mode

Using the page mode, you can construct a comprehensive API documentation for a package. The following YAML is `nav` part of MkApi's own `mkdocs.yml`:

~~~yaml
nav:
  - index.md
  - Examples:
    - google_style.md
    - numpy_style.md
  - API: mkapi/api/mkapi
~~~

MkApi scans the `nav` to find an entry that starts with `'mkapi/'`. This entry must includes two or more slashs (`'/'`). Second string (`'api'`) splitted by slash is a directory name. MkApi automatically creates this directory in the `docs` directory at the beginning of the process and deletes after the process.
The rest string(`'mkapi'`) is a directory path to a package that exists in the config directory. MkApi searches all packages and modules and create a Markdown source for one package or module, which is saved in the `api` directory. The rest work is done by MkDocs. You can see the API documentation of MkApi in nav area.

!!! note
    If a package or module has no package- or module-level docstring, MkApi doesn't process it.
