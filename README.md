[![PyPI version][pypi-image]][pypi-link]
[![Python versions][pyversions-image]][pyversions-link]
[![Travis][travis-image]][travis-link]
[![AppVeyor][appveyor-image]][appveyor-link]
[![Coverage Status][coveralls-image]][coveralls-link]
[![Code style: black][black-image]][black-link]

# MkApi

The MkApi plugin for [MkDocs](https://www.mkdocs.org/) generates API documentation for Python code. The MkApi plugin supports the [Google Python Style Guide](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) only and partially.

Features of the MkApi plugin are:

* Section syntax of the Goole style guide. Supported sections are `Args`, `Arguments`, `Attributes`, `Example[s]`, `Note[s]`, `Raises`, `Returns`, `References`, `Todo`, `Warning[s]`, `Warns`, and `Yields`.
* Type annotation. If you write your function such as `def func(x: int) -> str:`, you don't need write type(s) in `Args`, `Returns`, or `Yields` section again. You can overwrite the type annotation in the corresponding docstring.
* Object type inspection. The MkApi plugin creates `CLASS`, `DATACLASS`, `FUNCTION`, `GENERATOR`, `METHOD`, or `PROPERTY` prefix for each object.

## Quickstart

Install the plugin using pip:

```bash
pip install mkapi
```

Next, add the following lines to your `mkdocs.yml`:

```yml
plugins:
  - search # necessary for search to work
  - mkapi
```

Then, in your markdown file, add a tag to generate API docu
 for an package, module, or other objects.

```markdown
![mkapi](<something>)
```

For example, if you use PyTorch, you can check the functionality of MkApi:

```markdown
![mkapi](torch.optim)
```

## MkApi Documentation

See also: [MkApi Documentation](https://mkapi.daizutabi.net)


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
