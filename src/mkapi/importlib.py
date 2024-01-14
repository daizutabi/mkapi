"""importlib module."""
from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING

import mkapi.dataclasses
from mkapi import docstrings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Self

    from mkapi.docstrings import Docstring, Item, Section
    from mkapi.items import Attribute, Import, Parameter, Raise, Return


def load_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if name in modules:
        return modules[name]
    if not (path := get_module_path(name)):
        modules[name] = None
        return None
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    module = load_module_from_source(source, name)
    module.kind = "package" if path.stem == "__init__" else "module"
    modules[name] = module
    return module


def load_module_from_source(source: str, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from a source string."""
    node = ast.parse(source)
    module = create_module_from_node(node, name)
    module.source = source
    return module


# def get_object(fullname: str) -> Module | Class | Function | None:
#     """Return an [Object] instance by the fullname."""
#     if fullname in objects:
#         return objects[fullname]
#     for modulename in iter_parent_modulenames(fullname):
#         if load_module(modulename) and fullname in objects:
#             return objects[fullname]
#     objects[fullname] = None
#     return None


# LINK_PATTERN = re.compile(r"(?<!\])\[([^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


# def get_link(name: str, fullname: str) -> str:
#     """Return a markdown link."""
#     return f"[{name}][__mkapi__.{fullname}]"


# modules: dict[str, Module | None] = {}


# # def _postprocess(obj: Module | Class) -> None:
# #     _merge_docstring(obj)
# #     for func in obj.functions:
# #         _merge_docstring(func)
# #     for cls in obj.classes:
# #         _postprocess(cls)
# #         _postprocess_class(cls)


# # def _merge_item(obj: Attribute | Parameter | Return | Raise, item: Item) -> None:
# #     if not obj.type and item.type:
# #         # ex. list(str) -> list[str]
# #         type_ = item.type.replace("(", "[").replace(")", "]")
# #         obj.type = Type(mkapi.ast.create_expr(type_))
# #     obj.text = Text(item.text)  # Does item.text win?


# # def _new(
# #     cls: type[Attribute | Parameter | Raise],
# #     name: str,
# # ) -> Attribute | Parameter | Raise:
# #     args = (None, name, None, None)
# #     if cls is Attribute:
# #         return Attribute(*args, None)
# #     if cls is Parameter:
# #         return Parameter(*args, None, None)
# #     if cls is Raise:
# #         return Raise(*args)
# #     raise NotImplementedError


# # def _merge_items(cls: type, attrs: list, items: list[Item]) -> list:
# #     names = unique_names(attrs, items)
# #     attrs_ = []
# #     for name in names:
# #         if not (attr := get_by_name(attrs, name)):
# #             attr = _new(cls, name)
# #         attrs_.append(attr)
# #         if not (item := get_by_name(items, name)):
# #             continue
# #         _merge_item(attr, item)  # type: ignore
# #     return attrs_


# # def _merge_docstring(obj: Module | Class | Function) -> None:
# #     """Merge [Object] and [Docstring]."""
# #     if not obj.text:
# #         return
# #     sections: list[Section] = []
# #     for section in docstrings.parse(obj.text.str):
# #         if section.name == "Attributes" and isinstance(obj, Module | Class):
# #             obj.attributes = _merge_items(Attribute, obj.attributes, section.items)
# #         elif section.name == "Parameters" and isinstance(obj, Class | Function):
# #             obj.parameters = _merge_items(Parameter, obj.parameters, section.items)
# #         elif section.name == "Raises" and isinstance(obj, Class | Function):
# #             obj.raises = _merge_items(Raise, obj.raises, section.items)
# #         elif section.name in ["Returns", "Yields"] and isinstance(obj, Function):
# #             _merge_item(obj.returns, section)
# #             obj.returns.name = section.name
# #         else:
# #             sections.append(section)


# # ATTRIBUTE_ORDER_DICT = {
# #     ast.AnnAssign: 1,
# #     ast.Assign: 2,
# #     ast.FunctionDef: 3,
# #     ast.TypeAlias: 4,
# # }


# # def _attribute_order(attr: Attribute) -> int:
# #     if not attr.node:
# #         return 0
# #     return ATTRIBUTE_ORDER_DICT.get(type(attr.node), 10)


# def _iter_base_classes(cls: Class) -> Iterator[Class]:
#     """Yield base classes.

#     This function is called in postprocess for setting base classes.
#     """
#     if not cls.module:
#         return
#     for node in cls.node.bases:
#         base_name = next(mkapi.ast.iter_identifiers(node))
#         base_fullname = cls.module.get_fullname(base_name)
#         if not base_fullname:
#             continue
#         base = get_object(base_fullname)
#         if base and isinstance(base, Class):
#             yield base


# def _inherit(cls: Class, name: str) -> None:
#     # TODO: fix InitVar, ClassVar for dataclasses.
#     members = {}
#     for base in cls.bases:
#         for member in getattr(base, name):
#             members[member.name] = member
#     for member in getattr(cls, name):
#         members[member.name] = member
#     setattr(cls, name, list(members.values()))


# # def _postprocess_class(cls: Class) -> None:
# #     cls.bases = list(_iter_base_classes(cls))
# #     for name in ["attributes", "functions", "classes"]:
# #         _inherit(cls, name)
# #     if init := cls.get_function("__init__"):
# #         cls.parameters = init.parameters
# #         cls.raises = init.raises
# #         # cls.docstring = docstrings.merge(cls.docstring, init.docstring)
# #         cls.attributes.sort(key=_attribute_order)
# #         del_by_name(cls.functions, "__init__")
# #     if mkapi.dataclasses.is_dataclass(cls):
# #         for attr, kind in mkapi.dataclasses.iter_parameters(cls):
# #             args = (None, attr.name, None, None, attr.default, kind)
# #             parameter = Parameter(*args)
# #             parameter.text = attr.text
# #             parameter.type = attr.type
# #             parameter.module = attr.module
# #             cls.parameters.append(parameter)

# def get_globals(module: Module) -> dict[str, Class | Function | Attribute | Import]:
#     members = module.classes + module.functions + module.imports
#     globals_ = {member.fullname: member for member in members}
#     for attribute in module.attributes:
#         globals_[f"{module.name}.{attribute.name}"] = attribute  # type: ignore
#     return globals_
