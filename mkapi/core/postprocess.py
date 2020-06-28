from typing import Any, Dict, List, Optional

from mkapi.core.base import Inline, Item, Section, Type
from mkapi.core.node import Node
from mkapi.core.renderer import renderer
from mkapi.core.structure import Object


def sourcelink(object: Object) -> str:
    if "property" in object.kind:
        link = f'<span id="{object.id}"></span>'
    else:
        link = ""
    link += f'<a class="mkapi-src-link" href="../source/{object.module}'
    link += f'#{object.id}" title="Source for {object.id}">&lt;/&gt;</a>'
    return link


def source_link_from_section_item(item: Item, object: Object):
    link = sourcelink(object)

    def callback(inline, link=link):
        return inline.html + link

    item.description.callback = callback


def transform_property(node: Node, filters: List[str] = None):
    section = None
    members = []
    for member in node.members:
        object = member.object
        if "property" in object.kind:
            if section is None:
                section = node.docstring["Attributes"]
            name = object.name
            kind = object.kind
            type = object.type
            description = member.docstring.sections[0].markdown
            item = Item(name, type, Inline(description), kind=kind)
            if filters and "sourcelink" in filters:
                source_link_from_section_item(item, object)
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
            if name in node.docstring:
                section = node.docstring[name]
                if section.type:
                    name = section.type.name
                    break
        else:
            name = ""
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
        if member.docstring and "" in member.docstring:
            description = member.docstring[""].markdown
            if "\n\n" in description:
                description = description.split("\n\n")[0]
        else:
            description = ""
        item = Item(object.name, type, Inline(description), kind)
        item.markdown, url = "", ""
        if filters and ("link" in filters or "all" in filters):
            url = "#" + object.id
        elif filters and "apilink" in filters:
            url = "../" + node.object.id + "#" + object.id
        signature: Dict[str, Any] = {}
        if object.kind not in ["class", "dataclass"]:
            args = [item.name for item in object.signature.parameters.items]
            signature["arguments"] = args
        else:
            signature["arguments"] = None
        item.html = renderer.render_object_member(object.name, url, signature)
        if filters and "sourcelink" in filters:
            source_link_from_section_item(item, object)
        section.items.append(item)
    node.docstring.set_section(section)


def transform_class(node: Node, filters: Optional[List[str]] = None):
    if filters is None:
        filters = []
    transform_property(node, filters)
    transform_members(node, "class", ["link"] + filters)
    transform_members(node, "method", ["link"] + filters)


def transform_module(node: Node, filters: Optional[List[str]] = None):
    transform_members(node, "class", filters)
    transform_members(node, "function", filters)
    if not filters or "all" not in filters:
        node.members = []


def sort(node: Node):
    doc = node.docstring
    for section in doc.sections:
        if section.name in ["Classes", "Parameters"]:
            continue
        section.items = sorted(section.items, key=lambda x: x.name)


def transform(node: Node, filters: Optional[List[str]] = None):
    if node.object.kind.replace("abstract ", "") in ["class", "dataclass"]:
        transform_class(node, filters)
    elif node.object.kind in ["module", "package"]:
        transform_module(node, filters)
    for x in node.walk():
        sort(x)
    for member in node.members:
        transform(member, filters)
