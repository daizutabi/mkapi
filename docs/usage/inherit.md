# Docstring Inheritance

<style type="text/css">
<!--
.mkapi-node {   border: 2px dashed #88AA88; }
-->
</style>

```python hide
import sys

if '../../examples' not in sys.path:
  sys.path.insert(0, '../../examples')
import inherit
```

## Example classes

Define two classes to explain **Docstring inheritance**.

#File inherit.py {%=/examples/inherit.py%}

Docstring for `Base` class. Here, description for `type` is omitted on purpose.

~~~markdown
![mkapi](inherit.Base)
~~~

![mkapi](inherit.Base)

Next, `Item` subclass.

~~~markdown
![mkapi](inherit.Item)
~~~

![mkapi](inherit.Item|nocache)

## Inheritance from Superclasses

Since the docstring of superclass `Base` describes the `type`, the `Item` class can inherit its description with `inherit` filter.

~~~markdown
![mkapi](inherit.Item|inherit)
~~~

![mkapi](inherit.Item|inherit|nocache)

By inheritance from superclasses, you don't need to write duplicated description.

## Inheritance from Signature

Using `strict` filter, MkApi adds missing parameters and attributes from the signature. Description is still empty but type is inspected. Note that `strict` filter invokes `inherit` filter at the same time.

~~~markdown
![mkapi](inherit.Item|strict)
~~~

![mkapi](inherit.Item|strict|nocache)

Inheritance from signature has two benefits:

* You can find parameters and attributes that wait for description.
* Users can know their types at least if you use type annotation.

## Inheritance in Page Mode

Inheritance in [page mode](page.md) is straightforward. For example,

~~~yaml
nav:
  - index.md
  - API: mkapi/api/mkapi|upper|strict
~~~
