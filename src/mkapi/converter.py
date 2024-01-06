"""Converter."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkapi.objects import Module


def convert(module: Module) -> str:
    """Convert the [Module] instance to markdown text."""
    return f"# {module.name}"
