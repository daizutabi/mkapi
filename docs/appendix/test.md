# Test

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

#File a.py {%=/examples/appendix/a.py%}

#File b.py {%=/examples/appendix/b.py%}

![mkapi](appendix.a.A)

![mkapi](appendix.b.B)

![mkapi](appendix.b.C)


```python
from examples.appendix.b import C
from mkapi.core.node import get_members

get_members(C)
```

```python
dir(C.a)
```

```python
bases = C.mro()
import inspect
import importlib
sourfiles = []
for base in bases[:-1]:
  try:
    sourfiles.append(inspect.getsourcefile(base))
  except TypeError:
    pass
sourfiles  

```
