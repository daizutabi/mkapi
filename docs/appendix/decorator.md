# Decorators


<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

#File appendix/decorator.py {%=/examples/appendix/decorator.py%}

#File appendix/decorated.py {%=/examples/appendix/decorated.py%}

```python
import inspect

from appendix.decorated import func_with_wraps, func_without_wraps

funcs = [func_with_wraps, func_without_wraps]
for func in funcs:
    sourcefile = inspect.getsourcefile(func)
    is_wrapped = hasattr(func, '__wrapped__')
    print(f"[{func.__name__}]: {sourcefile}, {is_wrapped}")
```


~~~markdown
## ![mkapi](appendix.decorated|all)
~~~

## ![mkapi](appendix.decorated|all)
