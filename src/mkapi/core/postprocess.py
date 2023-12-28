"""Postprocess."""
from mkapi.core.base import Inline, Item, Section, Type
from mkapi.core.node import Node
from mkapi.core.renderer import renderer
from mkapi.core.structure import Object


def sourcelink(obj: Object) -> str:  # noqa: D103
    link = f'<span id="{obj.id}"></span>' if "property" in obj.kind else ""
    link += f'<a class="mkapi-src-link" href="../source/{obj.module}/'
    link += f'#{obj.id}" title="Source for {obj.id}">&lt;/&gt;</a>'
    return link


def source_link_from_section_item(item: Item, obj: Object) -> None:  # noqa: D103
    link = sourcelink(obj)

    def callback(inline: Inline, link: str = link) -> str:
        return inline.html + link

    item.description.callback = callback


def transform_property(node: Node, filters: list[str] | None = None) -> None:  # noqa: D103
    section, members = None, []
    for member in node.members:
        obj = member.object
        if "property" in obj.kind:
            if section is None:
                section = node.docstring["Attributes"]
            description = member.docstring.sections[0].markdown
            item = Item(obj.name, obj.type, Inline(description), kind=obj.kind)
            if filters and "sourcelink" in filters:
                source_link_from_section_item(item, obj)
            section.items.append(item)
        else:
            members.append(member)
    node.members = members


def get_type(node: Node) -> Type:  # noqa: D103
    if type_ := node.object.type:
        return Type(type_.name)
    for name in ["Returns", "Yields"]:
        if name in node.docstring and (section := node.docstring[name]).type:
            return Type(section.type.name)
    return Type()


def get_description(member: Node) -> str:  # noqa: D103
    if member.docstring and "" in member.docstring:
        description = member.docstring[""].markdown
        return description.split("\n\n")[0]
    return ""


def get_url(node: Node, obj: Object, filters: list[str]) -> str:  # noqa: D103
    if "link" in filters or "all" in filters:
        return "#" + obj.id
    if filters and "apilink" in filters:
        return "../" + node.object.id + "#" + obj.id
    return ""


def get_arguments(obj: Object) -> list[str] | None:  # noqa: D103
    if obj.kind not in ["class", "dataclass"]:
        return [item.name for item in obj.signature.parameters.items]
    return None


def transform_members(node: Node, mode: str, filters: list[str] | None = None) -> None:  # noqa: D103
    def is_member(kind: str) -> bool:
        if mode in ["method", "function"]:
            return mode in kind or kind == "generator"
        return mode in kind and "method" not in kind

    members = [member for member in node.members if is_member(member.object.kind)]
    if not members:
        return

    name = mode[0].upper() + mode[1:] + ("es" if mode == "class" else "s")
    section = Section(name)
    for member in members:
        obj = member.object
        description = get_description(member)
        item = Item(obj.name, get_type(member), Inline(description), obj.kind)
        url = get_url(node, obj, filters) if filters else ""
        signature = {"arguments": get_arguments(obj)}
        item.html = renderer.render_object_member(obj.name, url, signature)
        item.markdown = ""
        if filters and "sourcelink" in filters:
            source_link_from_section_item(item, obj)
        section.items.append(item)
    node.docstring.set_section(section)


def transform_class(node: Node, filters: list[str] | None = None) -> None:  # noqa:D103
    if filters is None:
        filters = []
    transform_property(node, filters)
    transform_members(node, "class", ["link", *filters])
    transform_members(node, "method", ["link", *filters])


def transform_module(node: Node, filters: list[str] | None = None) -> None:  # noqa: D103
    transform_members(node, "class", filters)
    transform_members(node, "function", filters)
    if not filters or "all" not in filters:
        node.members = []


def sort_sections(node: Node) -> None:  # noqa: D103
    for section in node.docstring.sections:
        if section.name not in ["Classes", "Parameters"]:
            section.items = sorted(section.items, key=lambda x: x.name)


def transform(node: Node, filters: list[str] | None = None) -> None:  # noqa: D103
    if node.object.kind.replace("abstract ", "") in ["class", "dataclass"]:
        transform_class(node, filters)
    elif node.object.kind in ["module", "package"]:
        transform_module(node, filters)
    for x in node.walk():
        sort_sections(x)
    for member in node.members:
        transform(member, filters)
