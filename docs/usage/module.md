# Module and Package

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

MkAPI can create module and package documentation as well as function and class. Specify a package or module by its full path name.

~~~
![mkapi](!!mkapi.core)
~~~

![mkapi](mkapi.core)


## Module Level Components

As class level attributes, module level attributes can be inspected. Here is the beginning part of `google_style.py`.

#File google_style.py: line number 1-18 {%=/examples/google_style.py[:18]%}

Although there is no Attributes section in docstring, MkAPI automatically creates the section if attributes are correctly documented.

~~~
![mkapi](google_style)
~~~

![mkapi](google_style)

Furthermore, Classes and Functions sections are also created that display a list of members defined in the module and their short descriptions. The prefix [D] means dataclass and [G] means generator.

## Documentation with Heading

The other method to create module documentation is heading. For example,

~~~
### ![mkapi](google_style)
~~~

create a `<h3>` tag for the `google_style` module.

### ![mkapi](google_style)

If you prefer upper case heading, use the `upper` filter.

~~~
### ![mkapi](google_style|upper)
~~~

### ![mkapi](google_style|upper)


## Display Members

`all` filter generates entire module documentation including class and function members. Note that Classes and Functions sections have links to the members.

~~~
### ![mkapi](google_style|upper|all)
~~~

### ![mkapi](google_style|upper|all)
