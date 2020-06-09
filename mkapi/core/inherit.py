"""This module implements the functionality of docstring inheritance."""
from typing import Dict, Iterator, List, Tuple

from mkapi.core.base import Item, Section, Type
from mkapi.core.node import Node, get_node


def get_params(node: Node, name: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Returns a tuple of (docstring params, signature params).

    Each params is a dictionary of name-type mapping.

    Args:
        node: Node instance.
        name: Section name: `Parameters` or  `Attributes`.

    Examples:
        >>> node = get_node('mkapi.core.base.Type')
        >>> doc_params, sig_params = get_params(node, 'Parameters')
        >>> doc_params
        {}
        >>> sig_params
        {'name': 'str, optional', 'markdown': 'str, optional'}
    """
    section = node.docstring[name]
    if section is None:
        docstring_params = {}
    else:
        docstring_params = {item.name: item.type.name for item in section.items}
    signature_params = node.object.signature[name]
    return docstring_params, signature_params


def is_complete(node: Node, name: str = "") -> bool:
    """Returns True if docstring is complete.

    Args:
        node: Node instance.
        name: Section name: 'Parameters' or  'Attributes', or ''.
            If name is '', both sections are checked.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> node = Node(get_object('mkapi.core.base.Base'))
        >>> is_complete(node, 'Parameters')
        True
        >>> node = Node(get_object('mkapi.core.base.Type'))
        >>> is_complete(node)
        False
    """
    if not name:
        return all(is_complete(node, name) for name in ["Parameters", "Attributes"])

    docstring_params, signature_params = get_params(node, name)
    for param in signature_params:
        if param not in docstring_params:
            return False
    return True


def inherit_base(node: Node, base: Node, name: str = ""):
    """Inherits Parameters or Attributes section from base class.

    Args:
        node: Node instance.
        base: Node instance of a super class.
        name: Section name: 'Parameters' or  'Attributes', or ''.
            If name is '', both sections are inherited.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> base = Node(get_object('mkapi.core.base.Base'))
        >>> node = Node(get_object('mkapi.core.base.Type'))
        >>> [item.name for item in base.docstring['Parameters'].items]
        ['name', 'markdown']
        >>> node.docstring['Parameters'] is None
        True
        >>> inherit_base(node, base)
        >>> [item.name for item in node.docstring['Parameters'].items]
        ['name', 'markdown']
    """
    if not name:
        for name in ["Parameters", "Attributes"]:
            inherit_base(node, base, name)
        return

    base_section = base.docstring[name]
    if base_section is None:
        return
    _, node_params = get_params(node, name)
    _, base_params = get_params(base, name)
    node_section = node.docstring[name]
    items = []
    for item in base_section.items:
        if node_section is None or item.name not in node_section:
            if (
                item.name in node_params
                and node_params[item.name] == base_params[item.name]
            ):
                items.append(item)
    if node_section is not None:
        for item in node_section.items:
            if item not in items:
                items.append(item)
    node.docstring[name] = Section(name, items=items)  # type:ignore


def inherit_signature(node: Node, name: str = ""):
    """Inherits Parameters or Attributes section from signature.

    Args:
        node: Node instance.
        name: Section name: 'Parameters' or  'Attributes', or ''.
            If name is '', both sections are inherited.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> base = Node(get_object('mkapi.core.base.Base'))
        >>> [item.name for item in base.docstring['Attributes'].items]
        ['html']
        >>> inherit_signature(base)
        >>> [item.name for item in base.docstring['Attributes'].items]
        ['name', 'markdown', 'html']
    """
    if not name:
        for name in ["Parameters", "Attributes"]:
            inherit_signature(node, name)
        return

    _, params = get_params(node, name)
    if not params:
        return

    node_section = node.docstring[name]
    items = []
    for item_name, type in params.items():
        if node_section is None or item_name not in node_section:
            item = Item(item_name, markdown="", type=Type(type))
        else:
            item = node_section[item_name]  # type:ignore
        items.append(item)
    node.docstring[name] = Section(name, items=items)


def inherit_parameters(node: Node):
    """Attributes section inherits items' markdown from Parameters section.

    Args:
        node: Node instance.

    Note:
        This function does not create any items. Call [inherit_signature]()() first.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> base = Node(get_object('mkapi.core.base.Base'))
        >>> node = Node(get_object('mkapi.core.base.Type'))
        >>> [item.name for item in base.docstring['Attributes'].items]
        ['html']
        >>> inherit_signature(base)
        >>> section = base.docstring['Attributes']
        >>> [item.name for item in section.items]
        ['name', 'markdown', 'html']
        >>> section['name'].markdown
        ''
        >>> inherit_parameters(base)
        >>> section['name'].markdown != ''
        True
    """
    param_section = node.docstring["Parameters"]
    attr_section = node.docstring["Attributes"]
    if param_section is None or attr_section is None:
        return
    for item in attr_section.items:
        if not item.markdown and item.name in param_section:
            item.markdown = param_section[item.name].markdown  # type:ignore


def get_bases(node: Node) -> Iterator[Tuple[Node, Iterator[Node]]]:
    """Yields a tuple of (Node instance, iterator of Node).

    Args:
        node: Node instance.

    Examples:
        >>> from mkapi.core.object import get_object
        >>> node = Node(get_object('mkapi.core.base.Type'))
        >>> it = get_bases(node)
        >>> n, gen = next(it)
        >>> n is node
        True
        >>> [x.object.name for x in gen]
        ['Base']
        >>> for n, gen in it:
        ...     if n.object.name == 'set_html':
        ...         break
        >>> [x.object.name for x in gen]
        ['set_html']
    """
    bases = node.obj.mro()[1:-1]
    yield node, (get_node(base) for base in bases)
    for member in node.members:
        name = member.object.name

        def gen(name=name):
            for base in bases:
                if hasattr(base, name):
                    obj = getattr(base, name)
                    if hasattr(obj, "__module__"):
                        yield get_node(getattr(base, name))

        yield member, gen()


def inherit(node: Node, strict: bool = False):
    """Inherits Parameters and Attributes from superclasses.

    This function calls [inherit_base]()(), [inherit_signature]()(),
    [inherit_parameters]()().

    Args:
        node: Node instance.
        strict: If True, inherits from signature, too.
     """
    for node, bases in get_bases(node):
        if is_complete(node):
            continue
        for base in bases:
            inherit_base(node, base)
            if is_complete(node):
                break
        if strict:
            inherit_signature(node)
            if node.object.kind == "dataclass":
                inherit_parameters(node)


def inherit_by_filters(node: Node, filters: List[str]):
    """Inherits Parameters and Attributes from superclasses.

    Args:
        node: Node instance.
        filters: Chose fileters. 'inherit' for superclass inheritance or 'strict'
            for signature inheritance.
     """
    if node.object.kind in ["class", "dataclass"]:
        if "inherit" in filters:
            inherit(node)
        elif "strict" in filters:
            inherit(node, strict=True)
    elif "strict" in filters and node.object.signature.signature:
        inherit_signature(node, "Parameters")
