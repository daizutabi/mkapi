"""md
# Using MkApi within Python

MkApi is a standalone library as well as a MkDocs plugin, so that you can use it
within Python.

First, import MkApi:

{{ # cache:clear }}
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

    def to_str(self, x: int) -> str:
        """Converts `int` to `str`.

        Args:
            x: Input value.
        """
        return str(x)


# `mkapi.get_node()` generates a `Node` object that has tree structure.

# -
node = mkapi.get_node(A)
type(node)

# Some attributes:

node.kind, node.name
# -
docstring = node.docstring
len(docstring.sections)  # type:ignore
# -
section = docstring.sections[0]  # type:ignore
section.name, section.markdown
# -
section = docstring.sections[1]  # type:ignore
section.name, section.markdown

# The `members` attribute gives children, for example, bound methods of a class.

len(node.members)
# -
child = node.members[0]
type(child)

# Elements of `Node.members` are also `Node` objects, so this is a tree structure.

child.kind, child.name
# -
docstring = child.docstring
len(docstring.sections)  # type:ignore
# -
section = docstring.sections[0]  # type:ignore
section.name, section.markdown
# -
section = docstring.sections[1]  # type:ignore
section.name, section.markdown

# The above Parameters section has an empty `markdown`, while its `items` represent
# argument list:

section.items

# You can see that the type of argument `x` is inspected. Note that the `markdown`
# attribute is set from docstring, while the `html` attribute is empty.

# `Node.get_markdown()` creates a *joint* Markdown of this node.

markdown = node.get_markdown()
print(markdown)

# Where is Note or Parameters section header, *etc.*? No problem. The
# `Node.get_markdown()` divides docstring into two parts. One is a plain Markdown that
# will be converted into HTML by any Markdown converter, for example, MkDocs. The other
# is the outline structure of a docstring such as sections or arguments that will be
# processed by MkApi itself.

# ## Converting Markdown

# For simplicity, we use [Python-Markdown](https://python-markdown.github.io/) library
# instead of `MkDocs`.

from markdown import Markdown  # isort:skip

converter = Markdown()
html = converter.convert(markdown)
print(html)


# ## Distributing HTML

# `Node.set_html()` distributes HTML into docstring and members.

node.set_html(html)

# Take a look at what happened.

section = node.docstring.sections[0]  # type:ignore
section.markdown, section.html
# -
section = node.docstring.sections[1]  # type:ignore
section.markdown, section.html
# -
child = node.members[0]
section = child.docstring.sections[0]  # type:ignore
section.markdown, section.html
# -
section = child.docstring.sections[1]  # type:ignore
item = section.items[0]
item.markdown, item.html  # A <p> tag is deleted.

# ## Constructing HTML

# Finally, construct one HTML calling `Node.render()` that internally uses
# [Jinja](https://jinja.palletsprojects.com/en/2.11.x/) library.

html = node.render()
print(html[:300].strip())

# [Jupyter](https://jupyter.org/) allows us to see the rendered HTML.

from IPython.display import HTML  # isort:skip

HTML(html)
