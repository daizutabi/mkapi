# import inspect
# from dataclasses import dataclass
#
# import mkapi
#
#
# @dataclass
# class Base:
#     """Base class.
#
#     Parameters:
#         name: Object name.
#         type: Object type
#
#     Attributes:
#         name: Object name.
#         type: Object type
#     """
#
#     name: str
#     type: str = ""
#
#
# @dataclass
# class Item(Base):
#     """Item class.
#
#     Parameters:
#         markdown: Object markdown
#
#     Attributes:
#         markdown: Object markdown
#     """
#
#     markdown: str = ""
#
#
#
#
# node = mkapi.get_node(Item)
# node.signature.signature.parameters
#
# inspect.signature(Item).parameters
#
# node.parameters.items
# from mkapi.core.base import Node
#
#
# def is_complete(node: Node):
#     inspect_parameters = node.signature.signature.parameters
#     if not len(inspect_parameters):
#         return True
#     node_parameters = node.parameters
#     if not node_parameters:
#         return False
#
#     node_parameters_name = [item.name for item in node_parameters]
#     return node_parameters_name
#
# is_complete(node)
# node.signature.attributes
