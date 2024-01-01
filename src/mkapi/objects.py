# """Object class."""
# from __future__ import annotations

# import ast
# from dataclasses import dataclass
# from typing import TYPE_CHECKING, TypeAlias

# from mkapi.ast import iter_def_nodes

# if TYPE_CHECKING:
#     from collections.abc import Iterator
#     from pathlib import Path

#     from mkapi.modules import Module


# Node: TypeAlias = ast.ClassDef | ast.Module | ast.FunctionDef


# @dataclass
# class Object:
#     """Object class."""

#     name: str
#     path: Path
#     source: str
#     module: Module
#     node: Node


# def iter_objects(module: Module) -> Iterator:
#     pass
