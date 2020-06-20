# Docstring Inheritance

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
  margin-left: 0px;
  margin-bottom: 20px;
}
-->
</style>

```python hide
import sys

if '../../examples' not in sys.path:
  sys.path.insert(0, '../../examples')
import inherit
```

Define two classes to explain **Docstring inheritance**.

#File inherit.py {%=/examples/inherit.py%}

Taking a look at this example, you may notice that:

* In the `Base`, there is no description for `type`.
* In the `Item`, parameters inherited from the superclass are not written.
* In the `Item.set_name()`, Parameters section itself doesn't exist.
* In the `Base.set()`, `{class}` variable is used to replace it by class name.

## Inheritance from Superclasses

Since the docstring of the superclass `Base` describes the `name`, the `Item` class can inherit its description.

~~~markdown
![mkapi](inherit.Item)
~~~

![mkapi](inherit.Item)

By inheritance from superclasses, you don't need to write duplicated description.

## Inheritance from Signature

Using `strict` filter, MkApi also adds parameters and attributes without description using its signature. Description is still empty but type is inspected.

~~~markdown
![mkapi](inherit.Item|strict)
~~~

![mkapi](inherit.Item|strict)

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

## Inheritance in Dataclass


#File inherit_comment.py {%=/examples/inherit_comment.py%}

~~~
![mkapi](inherit_comment.Item)
~~~

![mkapi](inherit_comment.Item)
