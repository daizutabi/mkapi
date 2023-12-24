# Inheritance and Special Methods

## Examples

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

#File appendix/inherit.py {%=/examples/appendix/inherit.py%}

### Superclass

~~~markdown
![mkapi](appendix.inherit.Base)
~~~

![mkapi](appendix.inherit.Base)

### Subclass

~~~markdown
![mkapi](appendix.inherit.Sub)
~~~

![mkapi](appendix.inherit.Sub)

## Implementation

There are two ways to get docstring: `__doc__` attribute or `inspect.getdoc()`.

```python hide
import sys
sys.path.insert(0, 'examples')
```

```python
import inspect
from appendix.inherit import Base, Sub

Base.func.__doc__, inspect.getdoc(Base.func)
```

```python
Sub.func.__doc__, inspect.getdoc(Sub.func)
```

Because `Sub.func()` has no docstring, its `__doc__` attribute is `None`. On the other hand, the super class `Base.func()` has docstring, so that you can get the *inherited* docstring using `inspect.getdoc()`. Therefore, MkAPI uses `inspect.getdoc()`.

Now, let's see some special methods:

```python
Sub.__call__.__doc__, inspect.getdoc(Sub.__call__)
```

```python
Sub.__repr__.__doc__, inspect.getdoc(Sub.__repr__)
```

```python
Sub.__repr__.__doc__, inspect.getdoc(Sub.__repr__)
```

These docstrings come from `object`.

```python
for name, obj in object.__dict__.items():
    doc = obj.__doc__
    if doc and '\n' not in doc:
        print(f"{name}: {doc}")
```

If docstring of an object is equal to that of `object`, the object doesn't be added into API documentation.
