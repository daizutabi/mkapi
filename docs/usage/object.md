# Object mode

## `examples` package

<style type="text/css">
.mkapi-container {
  border: dashed #88AA8877;
}
</style>

[Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google)

[Example NumPy Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy)

``` sh
examples/
├─ __init__.py
└─ styles/
   ├─ __init__.py
   ├─ example_google.py
   └─ example_numpy.py
```

## Package

```markdown
::: __mkapi__.examples
```

::: examples

!!! note
    In the above example, green dashed border lines are just guide
    for the eye to show the region of the documentation generated
    by MkAPI.

```markdown
::: __mkapi__.examples|source|bare
```

::: examples|source|bare

## Package with `__all__`

```markdown
::: __mkapi__.examples.styles
```

::: examples.styles

::: examples.styles|source|bare

## Module

```markdown
::: __mkapi__.examples.styles.example_google
```

::: examples.styles.example_google

!!! warning
    MkAPI doesn't support reStructuredText formatting.

## Module members

### Class

```markdown
::: __mkapi__.examples.styles.example_google.ExampleClass
```

::: examples.styles.example_google.ExampleClass

!!! warning
    "\_\_init\_\_" should be written in a inline code (\`\_\_init\_\_\`)
    or escaped (\\\_\\\_init\\\_\\\_).

### Function

```markdown
::: __mkapi__.examples.styles.example_google.module_level_function
```

::: examples.styles.example_google.module_level_function

### Attribute

```markdown
::: __mkapi__.examples.styles.example_google.module_level_variable2|sourcelink
```

::: examples.styles.example_google.module_level_variable2|sourcelink
