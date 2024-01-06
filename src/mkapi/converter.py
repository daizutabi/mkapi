"""Converter."""
from __future__ import annotations

from mkapi.objects import get_module

# from mkapi.renderer import renderer


def convert_module(name: str, filters: list[str]) -> str:
    """Convert the [Module] instance to markdown text."""
    # if module := get_module(name):
    #     return renderer.render_module(module)
    return f"{name} not found"


def convert_object(name: str, level: int) -> str:
    return "xxxx"


def convert_html(name: str, html: str, filters: list[str]) -> str:
    return "xxxx"
