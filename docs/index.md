# Home

MkAPI is a plugin for [MkDocs](https://www.mkdocs.org/) to generate
API documentation for your Python project.

MkAPI supports two styles of docstrings:
[Google](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
and
[NumPy](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).
See [Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/)
documentation for details.

## Features

- __Type annotation__: If you write your function such as
  `def func(x: int) -> str:`, you don't need write type(s)
  in Parameters, Returns, or Yields section again.
  You can override the type annotation in docstrings.
- __Object type inspection__: MkAPI plugin creates *class*,
  *dataclass*, *function*, *method*, *property* prefix for each object.
- __Docstring inheritance__: Docstring of a subclass can inherit parameters
  and attributes description from its superclasses.
- __Table of Contents__: Table of contents are inserted into the documentation
  of each package, module, and class.
- __Bidirectional Link__: Bidirectional links are created between
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
Object mode and Page mode.

### Object Mode

To generate the API documentation in a Markdown source,
add three colons + object full name.
The object can be a module, class, function, or attribute.

```markdown
::: package.module.object
```

The Object mode is useful to embed an object documentation
in an arbitrary position of a Markdown source.
For more details, see [Object mode](usage/object.md).

### Page Mode

Using the Page mode, you can construct a comprehensive API documentation
for your project.
You can get this powerful feature by just one line in `mkdocs.yml`:

```yaml
nav:
  - index.md
  - API: $api/package.***
```

For more details, see [Page mode](usage/page.md).
