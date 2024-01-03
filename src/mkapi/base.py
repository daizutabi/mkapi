"""Base class."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ast


@dataclass
class Node:
    """Node class."""

    _node: ast.AST
    name: str
    """Name of item."""
    docstring: str | None
    """Docstring of item."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"
