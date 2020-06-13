from typing import List, Optional

from mkapi.core.base import Item, Section, Type
from mkapi.core.node import Node
from mkapi.core.renderer import renderer


def transform_property(node: Node):
    section = node.docstring["Attributes"]
    members = []
    for member in node.members:
        if "property" in member.object.kind:
            if section is None:
                section = Section("Attributes")
                node.docstring["Attributes"] = section
            name = member.object.name
            kind = member.object.kind
            type = member.object.type
            markdown = member.docstring.sections[0].markdown
            item = Item(name, markdown, type=type, kind=kind)
            section.items.append(item)
        else:
            members.append(member)
    node.members = members


def get_type(node: Node) -> Type:
    type = node.object.type
    if type:
        name = type.name
    else:
        for name in ["Returns", "Yields"]:
            section = node.docstring[name]
            if section and section.type:
                name = section.type.name
                break
        else:
            name = ""
    if name.startswith("("):
        name = name[1:-1]
    return Type(name)


def transform_members(node: Node, mode: str, filters: Optional[List[str]] = None):
    def is_member(kind):
        if mode in ["method", "function"]:
            return mode in kind or kind == "generator"
        else:
            return mode in kind and "method" not in kind

    members = [member for member in node.members if is_member(member.object.kind)]
    if not members:
        return

    name = mode[0].upper() + mode[1:] + ("es" if mode == "class" else "s")
    section = Section(name)
    for member in members:
        object = member.object
        kind = object.kind
        type = get_type(member)
        section_ = member.docstring[""]
        if section_:
            markdown = section_.markdown
            if "\n\n" in markdown:
                markdown = markdown.split("\n\n")[0]
        item = Item(object.name, markdown, type=type, kind=kind)
        item.markdown, url, signature = "", "", ""
        if filters and "link" in filters:
            url = "#" + object.id
        elif filters and "apilink" in filters:
            url = "../" + node.object.id + "#" + object.id
        if object.kind not in ["class", "dataclass"]:
            signature = "(" + ",".join(object.signature.parameters.keys()) + ")"
        item.html = renderer.render_object_member(object.name, url, signature)
        section.items.append(item)
    node.docstring[name] = section


def transform_class(node: Node):
    transform_property(node)
    transform_members(node, "class", ["link"])
    transform_members(node, "method", ["link"])


def transform_module(node: Node, filters: Optional[List[str]] = None):
    transform_members(node, "class", filters)
    transform_members(node, "function", filters)
    node.members = []


def transform(node: Node, filters: Optional[List[str]] = None):
    if node.docstring is None:
        return
    if node.object.kind in ["class", "dataclass"]:
        transform_class(node)
    elif node.object.kind in ["module", "package"]:
        transform_module(node, filters)
