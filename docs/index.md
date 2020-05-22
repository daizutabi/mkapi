# MkApi Documentation

MkApi is a [MkDocs](https://www.mkdocs.org/) plugin for auto API documentation.
MkApi supports the [Google Python Style Guide](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) partially.

Features of MkApi are:

* Supported sections: `Args`, `Arguments`, `Attributes`, `Example(s)`, `Note(s)`, `Raises`, `Returns`, `References`, `Todo`, `Warning(s)`, `Warns`, `Yields`.
* Type annotation. If you write your function such as `def func(x: int) -> str:`, you don't need write type(s) in `Args`, `Returns`, or `Yields` section. You can overwrite them in your docstring.
* Automatic type detection. MkApi can create `CLASS`, `DATACLASS`, `FUNCTION`, `GENERATOR`, `METHOD`, or `PROPERTY` prefix for each object.

## Installation

Install the plugin using pip:

~~~bash
pip install mkapi
~~~

## MkDocs setting

Add the following lines to your `mkdocs.yml`:

~~~yml
plugins:
  - search
  - mkapi
~~~

!!! note
    If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set.

## MkApi usage

In your markdown file, write a link to an package, module, or other object, just like normal Markdown's image embedding:

~~~markdown
![mkapi](<object.qualname>)
~~~

MkApi imports the module, function, or any object that you specify. If they aren't in `sys.path`, configure `mkdocs.yml` like below:

~~~yml
plugins:
  - search
  - mkapi:
      src_dirs: [<path_1>, <path_2>, ...]
~~~

Here, `path_X`s are inserted to `sys.path`. `path_X`s are relative to `mkdocs.yml`.
