"""Functionality of docstring inheritance."""
from collections.abc import Iterator

from mkapi.core.base import Section
from mkapi.core.node import Node, get_node
from mkapi.core.object import get_mro


def get_section(node: Node, name: str, mode: str) -> Section:
    """Return a tuple of (docstring section, signature section).

    Args:
        node: Node instance.
        name: Section name: `Parameters` or `Attributes`.
        mode: Mode name: `Docstring` or `Signature`.

    Examples:
        >>> node = get_node("mkapi.core.base.Type")
        >>> section = get_section(node, "Parameters", "Docstring")
        >>> "name" in section
        True
        >>> section["name"].to_tuple()
        ('name', 'str, optional', '')
    """
    if mode == "Docstring":
        if name in node.docstring:
            return node.docstring[name]
        return Section(name)
    if hasattr(node.object.signature, name.lower()):
        return node.object.signature[name]
    return Section(name)


def is_complete(node: Node, name: str = "both") -> bool:
    """Return True if docstring is complete.

    Args:
        node: Node instance.
        name: Section name: 'Parameters' or  'Attributes', or 'both'.
            If name is 'both', both sections are checked.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> node = Node(get_object("mkapi.core.base.Base"))
        >>> is_complete(node, "Parameters")
        True
        >>> node = Node(get_object("mkapi.core.base.Type"))
        >>> is_complete(node)
        False
    """
    if name == "both":
        return all(is_complete(node, name) for name in ["Parameters", "Attributes"])

    doc_section = get_section(node, name, "Docstring")
    sig_section = get_section(node, name, "Signature")
    for item in sig_section.items:
        if item.name not in doc_section:
            return False
    if not doc_section:
        return True
    return all(item.description.name for item in doc_section.items)


def inherit_base(node: Node, base: Node, name: str = "both") -> None:
    """Inherit Parameters or Attributes section from base class.

    Args:
        node: Node instance.
        base: Node instance of a super class.
        name: Section name: 'Parameters' or  'Attributes', or 'both'.
            If name is 'both', both sections are inherited.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> base = Node(get_object("mkapi.core.base.Base"))
        >>> node = Node(get_object("mkapi.core.base.Type"))
        >>> node.docstring["Parameters"]["name"].to_tuple()
        ('name', 'str, optional', '')
        >>> inherit_base(node, base)
        >>> node.docstring["Parameters"]["name"].to_tuple()
        ('name', 'str, optional', 'Name of self.')
    """
    if name == "both":
        for name in ["Parameters", "Attributes"]:
            inherit_base(node, base, name)
        return

    base_section = get_section(base, name, "Docstring")
    node_section = get_section(node, name, "Docstring")
    section = base_section.merge(node_section, force=True)
    if name == "Parameters":
        sig_section = get_section(node, name, "Signature")
        items = [item for item in section.items if item.name in sig_section]
        section.items = items
    if section:
        node.docstring.set_section(section, replace=True)


def get_bases(node: Node) -> Iterator[tuple[Node, Iterator[Node]]]:
    """Yields a tuple of (Node instance, iterator of Node).

    Args:
        node: Node instance.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> node = Node(get_object("mkapi.core.base.Type"))
        >>> it = get_bases(node)
        >>> n, gen = next(it)
        >>> n is node
        True
        >>> [x.object.name for x in gen]
        ['Inline', 'Base']
    """
    bases = get_mro(node.obj)[1:]
    yield node, (get_node(base) for base in bases)
    for member in node.members:
        name = member.object.name

        def gen(name: str = name) -> Iterator[Node]:
            for base in bases:
                if hasattr(base, name):
                    obj = getattr(base, name)
                    if hasattr(obj, "__module__"):
                        yield get_node(getattr(base, name))

        yield member, gen()


def inherit(node: Node) -> None:
    """Inherit Parameters and Attributes from superclasses.

    Args:
        node: Node instance.
    """
    if node.object.kind not in ["class", "dataclass"]:
        return
    for node_, bases in get_bases(node):
        if is_complete(node_):
            continue
        for base in bases:
            inherit_base(node_, base)
            if is_complete(node_):
                break
