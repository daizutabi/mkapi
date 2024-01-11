"""Converter."""
from __future__ import annotations

from mkapi.objects import load_module

# from mkapi.renderer import renderer


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
