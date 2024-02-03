# Embedding mode

## Example package

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

```markdown
::: __mkapi__.examples.styles
```

## Package with \_\_all\_\_

::: examples.styles

::: examples.styles|source|bare

## Module

```markdown
::: __mkapi__.examples.styles.example_google
```

::: examples.styles.example_google
