# MkApi Documentation

The MkApi plugin for [MkDocs](https://www.mkdocs.org/) generates API documentation for Python code. The MkApi plugin supports the [Google Python Style Guide](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) only and partially.

Features of the MkApi plugin are:

* Section syntax of the Goole style guide. Supported sections are `Args`, `Arguments`, `Attributes`, `Example[s]`, `Note[s]`, `Raises`, `Returns`, `References`, `Todo`, `Warning[s]`, `Warns`, and `Yields`.
* Type annotation. If you write your function such as `def func(x: int) -> str:`, you don't need write type(s) in `Args`, `Returns`, or `Yields` section again. You can overwrite the type annotation in the corresponding docstring.
* Object type inspection. The MkApi plugin creates `CLASS`, `DATACLASS`, `FUNCTION`, `GENERATOR`, `METHOD`, or `PROPERTY` prefix for each object.

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
