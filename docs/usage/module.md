# Module and Package

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

MkApi can create module and package documentation as well as function and class.

## Embeding Documentation

Specify a package or module by its full path name.

~~~
![mkapi](!!mkapi.core)
~~~

![mkapi](mkapi.core)

~~~
![mkapi](!!mkapi.core.base)
~~~

![mkapi](mkapi.core.base)

Unlike function or class, API for its members is not created, so that
you can select members to show. Or you can use [Page mode](page.md) that allows us to get entire project API.

## Module Level Attribute

As class level attributes, module level attributes can be inspected. Here is the beginning part of `google_style.py`.

#File google_style.py: line number 1-18 {%=/examples/google_style.py[:18]%}

Although there is no Attributes section in docstring, MkApi automatically creates the section if attributes are correctly documented.

~~~
![mkapi](google_style)
~~~

![mkapi](google_style)


## Heading Documentation

The other method to create module API is heading. For example

~~~
### ![mkapi](google_style)
~~~

### ![mkapi](google_style)

If you prefer upper case heading, use the `upper` filter.

~~~
### ![mkapi](google_style|upper)
~~~

### ![mkapi](google_style|upper)
