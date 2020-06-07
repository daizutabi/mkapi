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


## Heading Documentation

The other method to create module API is heading. For example

~~~
### ![mkapi](!!mkapi.core.base)
~~~

### ![mkapi](mkapi.core.base)

If you prefer upper case heading, use the `upper` *filter*.

~~~
### ![mkapi](!!mkapi.core.base|upper)
~~~

### ![mkapi](mkapi.core.base|upper)
