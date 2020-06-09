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
![mkapi](appendix.inherit.Abstract)
~~~

![mkapi](appendix.inherit.Abstract)

### Subclass

~~~markdown
![mkapi](appendix.inherit.Concrete)
~~~

![mkapi](appendix.inherit.Concrete)

## Implementation

There are two ways to get docstring: `__doc__` attribute or `inspect.getdoc()`.

```python hide
import sys
sys.path.insert(0, 'examples')
```

```python
import inspect
from appendix.inherit import Abstract, Concrete

Abstract.func.__doc__, inspect.getdoc(Abstract.func)
```

```python
Concrete.func.__doc__, inspect.getdoc(Concrete.func)
```

Because `Concrete.func()` has no docstring, its `__doc__` attribute is `None`. On the other hand, the super class `Abstract.func()` has docstring, so that you can get the *inherited* docstring using `inspect.getdoc()`. Therefore, MkApi uses `inspect.getdoc()`.

Now, let's see some special methods:

```python
Concrete.__call__.__doc__, inspect.getdoc(Concrete.__call__)
```

```python
Concrete.__repr__.__doc__, inspect.getdoc(Concrete.__repr__)
```

```python
Concrete.__repr__.__doc__, inspect.getdoc(Concrete.__repr__)
```

These docstrings come from `object`.

```python
for name, obj in object.__dict__.items():
    doc = obj.__doc__
    if doc and '\n' not in doc:
        print(f"{name}: {doc}")
```

If docstring of an ojbect is equal to that of `object`, the object doesn't be added into API documentation.
