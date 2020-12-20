# Filters

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
  margin-left: 0px;
  margin-bottom: 20px;
}
-->
</style>

{{ # cache:clear }}

```python hide
import sys

if '../../examples' not in sys.path:
  sys.path.insert(0, '../../examples')
```

## List of Filters

### upper

Use upper case letters for package and module object.

~~~markdown
### ![mkapi](filter)
~~~

### ![mkapi](filter)

~~~markdown
### ![mkapi](filter|upper)
~~~

### ![mkapi](filter|upper)

### short

Remove prefix.

~~~markdown
![mkapi](filter.C)
~~~

![mkapi](filter.C)

~~~markdown
![mkapi](filter.C|short)
~~~

![mkapi](filter.C|short)

### short_nav


Remove prefix from nav items. For example,

```yaml
nav:
  - index.md
  - API: mkapi/api/mkapi|short_nav
```

### strict

Show parameters and attributes even if their description is missing.

~~~markdown
![mkapi](filter.func|strict)
~~~

![mkapi](filter.func|strict)


## Scope of Filters

### Page Scope

For page scope filters, use empty object.

~~~markdown
![mkapi](|short)
~~~
~~~markdown
![mkapi](filter.gen)
~~~
~~~markdown
![mkapi](filter.C)
~~~

![mkapi](|short)
![mkapi](filter.gen)
![mkapi](filter.C)

### Global Scope

In `mkdocs.yaml`, select global filters:

~~~yml
# mkdocs.yml
plugins:
  - search
  - mkapi:
      src_dirs: [examples]
      filters: [short, strict]
~~~
