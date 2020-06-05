from typing import Dict, Tuple

import mkapi
from mkapi.core.base import Item, Node, Section


def get_params(node: Node, name: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    section = node.docstring[name]
    if section is None:
        docstring_params = {}
    else:
        docstring_params = {item.name: item.type for item in section}
    signature_params = node.signature[name]
    return docstring_params, signature_params


def is_complete(node: Node, name: str = "") -> bool:
    if not name:
        return all(is_complete(node, name) for name in ["Parameters", "Attributes"])

    docstring_params, signature_params = get_params(node, name)
    for param in signature_params:
        if param not in docstring_params:
            return False
    return True


def inherit_base(node: Node, base: Node, name: str = ""):
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
    for item in base_section:
        if node_section is None or item.name not in node_section:
            if (
                item.name in node_params
                and node_params[item.name] == base_params[item.name]
            ):
                items.append(item)
    if node_section is not None:
        for item in node_section:
            if item not in items:
                items.append(item)
    node.docstring[name] = Section(name, items=items)  # type:ignore


def inherit_signature(node: Node, name: str = ""):
    if not name:
        for name in ["Parameters", "Attributes"]:
            inherit_signature(node, name)
        return

    _, params = get_params(node, name)
    if not params:
        return

    node_section = node.docstring[name]
    if node_section is None:
        items = []
    else:
        items = node_section.items
    for item_name, type in params.items():
        if node_section is None or item_name not in node_section:
            item = Item(item_name, type, markdown="MISSING")
            items.append(item)
    node.docstring[name] = Section(name, items=items)  # type:ignore


def inherit(node: Node):
    if is_complete(node):
        return
    for cls in node.obj.mro()[:-1]:
        base = mkapi.get_node(cls)
        inherit_base(node, base)
        if is_complete(node):
            return
    inherit_signature(node)
