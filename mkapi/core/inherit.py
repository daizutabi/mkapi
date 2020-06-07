# This module implements the functionality of docstring inheritance.
# Todo: Inheritance from method.
from typing import Dict, Tuple

from mkapi.core.base import Item, Section, Type
from mkapi.core.node import Node, get_node


def get_params(node: Node, name: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    section = node.docstring[name]
    if section is None:
        docstring_params = {}
    else:
        docstring_params = {item.name: item.type.name for item in section.items}
    signature_params = node.object.signature[name]
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
        for item in node_section.items:
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
    items = []
    for item_name, type in params.items():
        if node_section is None or item_name not in node_section:
            item = Item(item_name, markdown="", type=Type(type))
        else:
            item = node_section[item_name]  # type:ignore
        items.append(item)
    node.docstring[name] = Section(name, items=items)


def inherit(node: Node, strict: bool = False):
    if is_complete(node):
        return
    for cls in node.obj.mro()[:-1]:
        base = get_node(cls)
        inherit_base(node, base)
        if is_complete(node):
            return
    if strict:
        inherit_signature(node)
