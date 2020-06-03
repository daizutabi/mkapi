"""md
# Using MkApi within Python

MkApi is a normal library as well as a MkDocs plugin.

First, import the library.

{{ # cache:clear }}
"""

import mkapi

# ## Node object

# `mkapi.get_node()` generates a object tree structure.


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


# -
node = mkapi.get_node(A)
type(node)
# -
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

# The `members` attribute gives children.

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
# -
section.items

# `Node.get_markdown()` creates a joint Markdown for this node.

markdown = node.get_markdown()
print(markdown)

# Where is Note or Parameters section header, *etc.*? No problem. The
# `Node.get_markdown()` divides docstring into two parts. One is a plain Markdown that
# will be converted into HTML by any Markdown converter, for example, MkDocs. The other
# is the outline of a docstring structure such as sections or arguments that is
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
section.markdown
# -
section.html
# -
section = node.docstring.sections[1]  # type:ignore
section.markdown
# -
section.html
# -
child = node.members[0]
section = child.docstring.sections[0]  # type:ignore
section.markdown
# -
section.html
# -
section = child.docstring.sections[1]  # type:ignore
section.items[0].markdown
# -
section.items[0].html  # A <p> tag is deleted.

# ## Constructing HTML

# Finally, construct one HTML using
# [Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) library.

html = node.render()
print(html[:300].strip())

# Using [Jupyter](https://jupyter.org/), we can display the rendered HTML.

from IPython.display import HTML
HTML(html)
