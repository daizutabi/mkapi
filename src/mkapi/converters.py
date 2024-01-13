"""Converter."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast

# from mkapi.converter import convert_html, convert_object
from mkapi.link import resolve_link
from mkapi.objects import load_module
from mkapi.utils import split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from mkapi.objects import Module


def convert_module(name: str, filters: list[str]) -> str:
    """Convert the [Module] instance to markdown text."""
    if module := load_module(name):
        #     return renderer.render_module(module)
        return f"{module}: {id(module)}"
    return f"{name} not found"


def convert_object(name: str, level: int) -> str:
    return "# ac"


def convert_html(name: str, html: str, filters: list[str]) -> str:
    return f"xxxx  {html}"
