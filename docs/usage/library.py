"""md
# Using MkApi within Python

MkApi is a standalone library as well as a MkDocs plugin, so that you can use it
within Python.

First, import MkApi:

{{ # cache:clear }}


<style type="text/css">  <!-- .mkapi-node {   border: 2px dashed #88AA88; } -->
</style>

"""


import mkapi

# ## Node object

# Define a simple class to show how MkApi works.


class A:
    """Class docstring.

    Note:
        Docstring of `__init__()` is deleted, if there is
        a class-level docstring.
    """

    def __init__(self):
        """Init docstring."""
        self.a: int = 1  #: Integer **attribute**.

    def to_str(self, x: int) -> str:
        """Converts `int` to `str`.

        Args:
            x: Input **value**.
        """
        return str(x)


# `mkapi.get_node()` generates a `Node` object that has tree structure.

# -
node = mkapi.get_node(A)
type(node)

# Some attributes:

node.object.kind, node.object.name
# -
docstring = node.docstring
len(docstring.sections)  # type:ignore
# -
section = docstring.sections[0]  # type:ignore
section.name
# -
print(section.markdown)
# -

# The `members` attribute gives children, for example, bound methods of a class.

len(node.members)
# -
child = node.members[0]
type(child)

# Elements of `Node.members` are also `Node` objects, so this is a tree structure.

child.object.kind, child.object.name
# -
docstring = child.docstring
len(docstring.sections)  # type:ignore
# -
section = docstring.sections[0]  # type:ignore
section.name, section.markdown
# -
section = docstring.sections[1]  # type:ignore
section.name, section.markdown

# The above Parameters section has an empty `markdown`, while its `items` represents an
# argument list:

item = section.items[0]
print(item)
print(item.type)
print(item.description)

# `Node.get_markdown()` creates a *joint* Markdown of this node.

markdown = node.get_markdown()
print(markdown)

# Where is Note or Parameters section heading, *etc.*? No problem. The
# `Node.get_markdown()` divides docstrings into two parts. One is a plain Markdown that
# will be converted into HTML by any Markdown converter, for example, MkDocs. The other
# is the outline structure of docstrings such as sections or arguments that will be
# processed by MkApi itself.

# ## Converting Markdown

# For simplicity, we use [Python-Markdown](https://python-markdown.github.io/) library
# instead of MkDocs.

from markdown import Markdown  # isort:skip

converter = Markdown(extensions=['admonition'])
html = converter.convert(markdown)
print(html)


# ## Distributing HTML

# `Node.set_html()` distributes HTML into docstring and members.

node.set_html(html)

# Take a look at what happened.

section = node.docstring.sections[0]  # type:ignore
section.markdown, section.html
# -
child = node.members[0]
section = child.docstring.sections[0]  # type:ignore
section.markdown, section.html
# -
section = child.docstring.sections[1]  # type:ignore
item = section.items[0]
item.description.markdown, item.description.html  # A <p> tag is deleted.

# ## Constructing HTML

# Finally, construct HTML calling `Node.get_html()` that internally uses
# [Jinja](https://jinja.palletsprojects.com/en/2.11.x/) library.

html = node.get_html()
print(html[:300].strip())

# [Jupyter](https://jupyter.org/) allows us to see the rendered HTML.

from IPython.display import HTML  # isort:skip

HTML(html)


# ## Summary

# All you need to get the documentation of an object is described by the following
# function.

from markdown import Markdown  # isort:skip

import mkapi  # isort:skip


def get_html(obj) -> str:
    # Construct a node tree structure.
    node = mkapi.get_node(obj)

    # Create a joint Markdown from components of the node.
    markdown = node.get_markdown()

    # Convert it into HTML by any external converter.
    converter = Markdown()
    html = converter.convert(markdown)

    # Split and distribute the HTML into original components.
    node.set_html(html)

    # Render the node to create final HTML.
    return node.get_html()
