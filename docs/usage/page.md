# Page Mode and Internal Links

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

## Page Mode

Page mode is a powerful feature that constructs a comprehensive API documentation for your project. To use the page mode, just add one line to `mkdocs.yml`:

~~~yaml
nav:
  - index.md
  - API: mkapi/api/mkapi
~~~

MkApi scans the `nav` to find an entry that starts with `'mkapi/'`. This entry must include two or more slashes (`'/'`). Second part (`'api'`) splitted by slash is a directory name. MkApi automatically creates this directory in the `docs` directory at the beginning of the process and deletes it and its contents after the process.

The rest (`'mkapi'`) is a root package name, which is assumed to exist in the `mkdocs.yml` directory. However, if a root package is in `src` directory, for example, you can specify it like this:

~~~yaml
  - API: mkapi/api/src/mkapi
~~~


MkApi searches all packages and modules and create a Markdown source for one package or module, which is saved in the `api` directory. The rest work is done by MkDocs. You can see the documentation of MkApi in the left navigation menu.

!!! note
    * If a package or module has no package- or module-level docstring, MkApi doesn't process it.
    * For upper case heading, use the `upper` filter. See [Documentation with Heading](../module/#documentation-with-heading).

## Internal Links

### Link from Markdown

Once a project documentation is generated, you can use hyperlink to it using normal Markdown syntax.

~~~markdown
Go to [Section](!!mkapi.core.base.Section).
~~~

The above line create a link to `mkapi.core.base.Section` object:

Go to [Section](mkapi.core.base.Section).

### Link from Docstring

You can use this feature even in your docstring. For example, assume that `func()` is defined in a `link.fullname` module:

#File link/fullname.py
~~~python
def func():
    """Internal link example.

    See Also:
        [a method](!!mkapi.core.base.Item.set_html)
    """
~~~

The `link.fullname.func()` is rendered as:

![mkapi](link.fullname.func)

You can click the above "a method" to visit its documentation.

Furthermore, if your module imports an object, you can refer it by its qualified name only.

#File link/qualname.py
~~~python
from mkapi.core.base import Section
from mkapi.core.docstring import get_docstring


def func():
    """Internal link example.

    * [Section]() --- Imported object.
    * [](get_docstring) --- Imported object.
    * [Section.set_html]() --- Member of imported object.
    * [Section definition](Section) --- Alternative text.
    """
    return Section(), get_docstring(None)
~~~

The `link.qualname.func()` is rendered as:

![mkapi](link.qualname.func)

### Link from Embedding Mode

Documentation created by the embedding mode has link to its project documentation.

~~~markdown
![mkapi](!!mkapi.core.docstring.section_heading)
~~~

creates the documentation of the `section_heading()`:

![mkapi](mkapi.core.docstring.section_heading)

You can click the prefix (`mkapi.core.docstring`) or the function name (`section_heading`) to go to the project documentation.


### Link from Type

[Docstring](mkapi.core.base.Docstring) class of MkApi has an attribute `sections` that is a list of `Section` class instance like below:

~~~python
# Mimic code of Docstring class.
from dataclasses import dataclass
from typing import List

from mkapi.core.base import Section

@dataclass
class Docstring:
    """Docstring ...."""
    sections: List[Section] = field(default_factory=list)
    type: str = ""
~~~

Corresponding *real* documentation is like below:

![mkapi](mkapi.core.base.Docstring)

Note that **Section** and **Type** are bold, which indicates that it is a link. Let's click. This link system using type annotation is useful to navigate users throughout the project documentation.
