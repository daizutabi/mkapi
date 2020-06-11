from mkapi.core.base import Item, Section
from mkapi.core.node import Node


def transform_property(node: Node):
    section = node.docstring["Attributes"]
    members = []
    for member in node.members:
        if "property" in member.object.kind:
            if section is None:
                section = Section("Attributes")
            name = member.object.name
            kind = member.object.kind
            type = member.object.type
            markdown = member.docstring.sections[0].markdown
            item = Item(name, markdown, type=type, kind=kind)
            section.items.append(item)
        else:
            members.append(member)
    node.members = members


# def transform_method(node: Node):
#     section = Section('Methods')
#     methods = []
#     markdown = 'abc'
#     for member in node.members:
#         name = member.object.name
#         id = member.object.id
#         kind = member.object.kind
#         type = member.object.type
#         print(name, id)
#         print(member.object.markdown)
#         # markdown = member.docstring.sections[0].markdown
#         # item = Item(name, markdown, type=type, kind=kind)
#         # section.items.append(item)
#
#     section.markdown = markdown
#     node.docstring['Methods'] = section


def transform_class(node: Node):
    if node.docstring is None:
        return
    transform_property(node)
    # transform_method(node)


def transform(node: Node):
    if node.object.kind in ["class", "dataclass"]:
        transform_class(node)
