# MkAPI Documentation

MkAPI is a plugin for MkDocs, designed to facilitate the generation
of API documentation for Python projects.
MkAPI streamlines the documentation process by automatically extracting
docstrings and organizing them into a structured format, making it easier
for developers to maintain and share their API documentation.

MkAPI supports two popular styles of docstrings: Google style and NumPy style,
allowing developers to choose the format that best fits their project's needs.

- Google Style: [Example Google Style Python Docstrings][google]
- NumPy Style: [Example NumPy Style Python Docstrings][numpy]

<!-- [napoleon]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/ -->
[google]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
[numpy]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html

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
[Object mode](usage/object.md) and [Page mode](usage/page.md).

### Object Mode

To generate the API documentation in a Markdown source, add three colons + object
full name. The object can be a function, class, or module.

```markdown
::: package.module.object
```

The Object mode is useful to embed an object's documentation
in an arbitrary position of a Markdown source.
For more details, see [Object mode](usage/object.md).

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

For more details, see [Page mode](usage/page.md).
