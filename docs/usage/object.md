# Object mode

## Demonstration package

In this page, we use a demonstration package: `examples`
to describe the Object mode of MkAPI.
This package includes one subpackage `styles`
and the `styles` subpackage includes two modules:
`google.py` and `numpy.py`
These two modules are style guides of docstrings:

- [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google)

- [Example NumPy Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy)

The directory structure of `examples` package is shown below:

``` sh
examples/
├─ __init__.py
└─ styles/
   ├─ __init__.py
   ├─ google.py
   └─ numpy.py
```

<style type="text/css">
.mkapi-container {
  border: dashed #22772288;
}
</style>

## Top level Package

First, let's see the top level package `examples`.
To embed the object documentation in a Markdown text,
you can write a Markdown syntax like:

```markdown
::: examples
```

The three collon (`:::`) must start at the begging of line,
followed by a space (` `) and an object fullname,
for example, `package.module.function`.
Here, just a pakcage name `examples`.
MkAPI finds this syntax in Markdown files and convert it
to the corresponding object documentation:

::: examples

!!! note
    In the above example, the green dashed border
    is just guide for the eye to show the region of
    the documentation generated by MkAPI.

In the above example, a horizontal gray line is an object
boundary to seperate successive objects.
A gray text above the line is the fullname
of the object.
Below the line, the object kind (*package*) and
(qualified) name (`examples`) are shown.
This part is a *heading* of documentation.

Below the heading, main contents of documentation
are rendered.
In the `examples` package case, the contents is a just
one-line summary for the package.

MkAPI can embed the source code of objects as well as their
documentation. For this, use *filters* like below:

```markdown
::: examples|source|bare
```

In this case, two filters `source` and `bare` are used.

- `source` ー Embed source code instead of documentation.
- `bare` ー Omit heading part so that only source code are shown.

The output is shown below:

::: examples|source|bare

The above docstring is the only content of `examples/__init__.py`.

## Package with `__all__`

A pakcage can have an `__all__` attribute to provide names
that should be imported when `from package import *` is encountered.
(See "[Importing * From a Package][1].")

[1]:
https://docs.python.org/3/tutorial/modules.html#importing-from-a-package>

MkAPI recognize the `__all__` attribute and automatically
list up the objects categorized by its kind
(*module*, *class*, *function*, or *attribute*).

In our example, `examples.styles` package have the `__all__` attribute.
Check the output:

```markdown
::: examples.styles
```

::: examples.styles

In the above example, `examples.styles` object documentation has
a **Classes** section that includes two classes:
`ExampleClassGoogle` and `ExampleClassNumpy`.
These names has a link to the object documentation to navigate you.
The summary line for a class is also shown for convinience.
Blow is the source code of `examples.styles/__init__.py`.

::: examples.styles|source|bare

Two classes have a diffrent class with the same name of `ExampleClass`.
`examples.styles` uses `import` statement with alias name
(`ExampleClassGoogle` or `ExampleClassNumpy`) to distinct these
two classes.
The **Classes** section shows these alias names, but you can check
the unaliased fullname by hovering mouse cursor on the names.

!!! Note
    Currently, MkAPI doesn't support dynamic assignment to `__all__`.
    For example, the below code are just ignored:

    ```python
    def get_all():
        return ["a", "b", "c"]

    __all__ = get_all()
    ```

## Module

Python module has classes, functions, or attributes as its members.
A Module documentation can be a docstring of module itself and members list.

```markdown
::: examples.styles.google
```

::: examples.styles.google

!!! warning
    MkAPI doesn't support reStructuredText formatting.

You can check the correspoing docstring
[here][examples.styles.google|source].

!!! note
    You can link Markdown text to object documentation or source:

    - `[here][examples.styles.google|source]`

## Module members

### Class

```markdown
::: examples.styles.google.ExampleClass
```

::: examples.styles.google.ExampleClass

!!! warning
    "\_\_init\_\_" should be written in a inline code (\`\_\_init\_\_\`)
    or escaped (\\\_\\\_init\\\_\\\_).

### Function

```markdown
::: examples.styles.google.module_level_function
```

::: examples.styles.google.module_level_function

### Attribute

```markdown
::: examples.styles.google.module_level_variable2|sourcelink
```

::: examples.styles.google.module_level_variable2|sourcelink