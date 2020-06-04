# Page Mode and Internal Links

<style type="text/css">
<!--
.mkapi-node-depth-0 {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

## Page Mode

Page mode is a powerful feature that constructs a comprehensive API documentation for a package. To use the page mode, just write one line in `mkdocs.yml`:

~~~yaml
nav:
  - index.md
  - API: mkapi/api/mkapi
~~~

MkApi scans the `nav` to find an entry that starts with `'mkapi/'`. This entry must includes two or more slashes (`'/'`). Second string (`'api'`) splitted by slash is a directory name. MkApi automatically creates this directory in the `docs` directory at the beginning of the process and deletes it and its contents after the process. The rest string (`'mkapi'`) is a directory path to a package relative to the `mkdocs.yml` directory. MkApi searches all packages and modules and create a Markdown source for one package or module, which is saved in the `api` directory. The rest work is done by MkDocs. You can see the API documentation of MkApi in the navigation menu.

!!! note
    If a package or module has no package- or module-level docstring, MkApi doesn't process it.

## Internal Links

Once a package API documentation is generated, you can use hyperlink to it using normal Markdown syntax.

~~~markdown
Click [Section](!mkapi.core.base.Section).
~~~

The above line create a link to `mkapi.core.base.Section` object:

Click [Section](mkapi.core.base.Section).

You can use this link even in your docstring. For example, assume that `func()` is defined in a `link` module:

~~~python
def func():
    """Internal link example.

    See Also:
        [Item](!mkapi.core.base.Item)
    """
~~~

The `func()` is rendered as:

```python hide
import sys

if '../../examples' not in sys.path:
  sys.path.insert(0, '../../examples')
import link
```

![mkapi](link.func)

You can click the above "Item" to visit its API.

## Link from Embedding Mode

API documentation created by the embedding mode has link to its package-level documentation.

~~~markdown
![mkapi](!mkapi.core.docstring.section_header)
~~~

creates API of the `section_header()`:

![mkapi](mkapi.core.docstring.section_header)

Then, you can click the prefix (`mkapi.core.docstring`) or the function name (`section_header`) to go to the package-level documentation.


## Link from Type

The `Docstring` class of MkApi has an attribute `sections` that is a list of `Section` class instance like below:

~~~python
from dataclasses import dataclass
from typing import List

from mkapi.core.base import Section

@dataclass
class Docstring:
    """Docstring ...."""
    sections: List[Section]
    type: str = ""
~~~

Then,

~~~markdown
![mkapi](!mkapi.core.base.Docstring)
~~~

creates API of the `Docstring` class:

![mkapi](mkapi.core.base.Docstring)

Note that `Section` is bold, which indicates that you can click. Let's click. (Or, you can check the fullname from a tooltip by hovering.)

As you can see, type annotation is useful to create automatic link to other objects.
