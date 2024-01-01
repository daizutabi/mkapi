# """Modules."""
# from __future__ import annotations

# import ast
# import re
# from dataclasses import dataclass
# from importlib.util import find_spec
# from pathlib import Path
# from typing import TYPE_CHECKING, TypeAlias

# import mkapi.ast.node
# from mkapi import config

# if TYPE_CHECKING:
#     from collections.abc import Iterator

# Def: TypeAlias = ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef
# Assign_: TypeAlias = ast.Assign | ast.AnnAssign
# Node: TypeAlias = Def | Assign_


# @dataclass
# class Module:
#     """Module class."""

#     name: str
#     path: Path
#     source: str
#     mtime: float
#     node: ast.Module

#     def __repr__(self) -> str:
#         class_name = self.__class__.__name__
#         return f"{class_name}({self.name!r})"

#     def is_package(self) -> bool:
#         """Return True if the module is a package."""
#         return self.path.stem == "__init__"

#     def update(self) -> None:
#         """Update contents."""

#     def get_node(self, name: str) -> Node:
#         """Return a node by name."""
#         nodes = mkapi.ast.node.get_nodes(self.node)
#         node = mkapi.ast.node.get_by_name(nodes, name)
#         if node is None:
#             raise NameError
#         return node

#     def get_names(self) -> dict[str, str]:
#         """Return a dictionary of names as (name => fullname)."""
#         return dict(mkapi.ast.node.iter_names(self.node))

#     def iter_submodules(self) -> Iterator[Module]:
#         """Yield submodules."""
#         if self.is_package():
#             for module in iter_submodules(self):
#                 yield module
#                 yield from module.iter_submodules()

#     def get_tree(self) -> tuple[Module, list]:
#         """Return the package tree structure."""
#         modules: list[Module | tuple[Module, list]] = []
#         for module in find_submodules(self):
#             if module.is_package():
#                 modules.append(module.get_tree())
#             else:
#                 modules.append(module)
#         return (self, modules)

#     def get_markdown(self, filters: list[str] | None) -> str:
#         """Return the markdown text of the module."""
#         return f"# {self.name}\n\n## {self.name}\n"
