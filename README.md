# MkAPI

[![PyPI Version][pypi-v-image]][pypi-v-link]
[![Python Version][python-v-image]][python-v-link]
[![Build Status][GHAction-image]][GHAction-link]
[![Coverage Status][codecov-image]][codecov-link]

MkAPI is a plugin for [MkDocs](https://www.mkdocs.org/),
designed to facilitate the generation
of API documentation for Python projects.
MkAPI streamlines the documentation process by automatically extracting
docstrings and organizing them into a structured format, making it easier
for developers to maintain and share their API documentation.

MkAPI supports two popular styles of documentation:
[Google style](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
and
[NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard),
allowing developers to choose the format that best fits their project's needs.
See the [Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/)
documentation for details about these two styles.

MkAPI is equipped with several key features that enhance the documentation
experience:

- **Type Annotation Support**: Automatically incorporates type annotations from
  function definitions into the documentation, reducing redundancy and
  improving clarity.
- **Object Type Inspection**: Analyzes Python objects to determine their types,
  enabling accurate representation in the documentation.
- **Docstring Inheritance**: Supports inheritance of docstring content from
  parent classes, ensuring that subclasses retain relevant documentation without
  duplication.
- **Automatic Table of Contents Generation**: Generates a table of contents for
  each package, module, and class, improving navigation within the
  documentation.
- **Bidirectional Links**: Creates links between the documentation and the source
  code, allowing users to easily navigate between the two.

MkAPI aims to simplify the documentation process, making it more efficient
and accessible for developers, while ensuring that the generated documentation
is comprehensive and easy to understand.

## Installation

Install the MkAPI plugin using pip:

```bash
pip install mkapi
```

MkAPI requires the following dependencies:

- Python 3.10 or higher
- MkDocs 1.6 or higher

## Configuration

To configure MkAPI, add the following lines to your `mkdocs.yml` file:

```yaml
plugins:
  - mkapi
```

## Usage

MkAPI provides two modes to generate API documentation:
Object mode and Page mode.


### Object Mode

To generate the API documentation in a Markdown source, add three colons + object
full name. The object can be a function, class, or module.

```markdown
::: package.module.object
```

The Object mode is useful to embed an object's documentation
in an arbitrary position of a Markdown source.
For more details, see [Object mode](https://daizutabi.github.io/mkapi/usage/object).

### Page Mode

Using the Page mode, you can construct comprehensive API documentation
for your project.
You can enable this powerful feature with just one line in `mkdocs.yml`:

```yaml
nav:
  - index.md
  - Reference:
    - $api/package.***
```

For more details, see [Page mode](https://daizutabi.github.io/mkapi/usage/page/).

<!-- Badges -->
[pypi-v-image]: https://img.shields.io/pypi/v/mkapi.svg
[pypi-v-link]: https://pypi.org/project/mkapi/
[python-v-image]: https://img.shields.io/pypi/pyversions/mkapi.svg
[python-v-link]: https://pypi.org/project/mkapi
[GHAction-image]: https://github.com/daizutabi/mkapi/actions/workflows/ci.yml/badge.svg?branch=main&event=push
[GHAction-link]: https://github.com/daizutabi/mkapi/actions?query=event%3Apush+branch%3Amain
[codecov-image]: https://codecov.io/github/daizutabi/mkapi/coverage.svg?branch=main
[codecov-link]: https://codecov.io/github/daizutabi/mkapi?branch=main
