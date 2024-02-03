# Home

[![PyPI version][pypi-image]][pypi-link]
[![Python versions][pyversions-image]][pyversions-link]
[![Code style: black][black-image]][black-link]

MkAPI plugin for [MkDocs](https://www.mkdocs.org/) generates
API documentation for Python code.

MkAPI supports two styles of docstrings:
[Google](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) and
[NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).

Features of MkAPI are:

* **Type annotation**: If you write your function such as
  `def func(x: int) -> str:`, you don't need write type(s)
  in Parameters, Returns, or Yields section again.
  You can overwrite the type annotation in the corresponding docstring.
* **Object type inspection**: MkAPI plugin creates *class*,
  *dataclass*, *function*, *method*, *property* prefix for each object.
* **Docstring inheritance**: Docstring of a subclass can inherit parameters
  and attributes description from its superclasses.
* **Table of Contents**: Table of contents are inserted into the documentation
  of each package, module, and class.
* **Bidirectional Link**: Bidirectional links are created between
  documentation and source code.

## Installation

Install the MkAPI plugin using pip:

```bash
pip install mkapi
```

## Configuration

Add the following lines to `mkdocs.yml`:

```yaml
plugins:
  - mkapi
```

## Usage

MkAPI provides two modes to generate API documentation:
Embedding mode and Page mode.

### Embedding Mode

To generate the API documentation in a Markdown source,
add three colons + object full name.
The object can be a function, class, attribute, or module.

```markdown
::: __mkapi__.package.module.object
```

You can combine this syntax with Markdown heading.

```markdown
## ::: __mkapi__.package.module.object
```

The embedding mode is useful to embed an object interface
in an arbitrary position of a Markdown source. For more details, see:

* [Google style examples](https://mkapi.daizutabi.net/examples/google_style)
* [NumPy style examples](https://mkapi.daizutabi.net/examples/numpy_style)

### Page Mode

Using the page mode, you can construct a comprehensive API documentation
for your project.
You can get this powerful feature by just one line:

```yaml
nav:
  - index.md
  - API: <api>/mkapi.***
```

For more details, see
[Page mode and internal links](https://mkapi.daizutabi.net/usage/page)

[pypi-image]: https://badge.fury.io/py/mkapi.svg
[pypi-link]: https://pypi.org/project/mkapi
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/ambv/black
[pyversions-image]: https://img.shields.io/pypi/pyversions/mkapi.svg
[pyversions-link]: https://pypi.org/project/mkapi
