"""Renderer class."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.importlib import add_sections_for_package, get_source
from mkapi.inspect import get_signature
from mkapi.objects import Attribute, Class, Function, Module

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load templates."""
    if not path:
        path = Path(mkapi.__file__).parent / "templates"
    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
    for name in os.listdir(path):
        templates[Path(name).stem] = env.get_template(name)


def render(
    obj: Module | Class | Function | Attribute,
    level: int,
    filters: list[str],
    *,
    is_source: bool = False,
) -> str:
    """Return a rendered Markdown."""
    heading = f"h{level}" if level else "p"
    prefix = obj.doc.type.markdown.split("..")
    self = obj.name.split(".")[-1].replace("_", "\\_")
    fullname = ".".join(prefix[:-1] + [self])
    id_ = obj.fullname.replace("_", "\\_")
    names = [x.replace("_", "\\_") for x in obj.qualname.split(".")]
    if isinstance(obj, Module):
        qualnames = [[x, "name"] for x in names]
    else:
        qualnames = [[x, "prefix"] for x in names]
        qualnames[-1][1] = "name"
    if isinstance(obj, Module) and obj.kind == "package":
        add_sections_for_package(obj)
    context = {
        "heading": heading,
        "id": id_,
        "fullname": fullname,
        "qualnames": qualnames,
        "obj": obj,
        "doc": obj.doc,
        "filters": filters,
    }
    if isinstance(obj, Module) and is_source:
        return _render_source(obj, context, filters)
    return _render_object(obj, context)


def _render_object(
    obj: Module | Class | Function | Attribute,
    context: dict[str, Any],
) -> str:
    if isinstance(obj, Class | Function):
        context["signature"] = get_signature(obj)
    return templates["object"].render(context)


def get_object_filter_for_source(
    obj: Module | Class | Function | Attribute,
    module: Module,
) -> str | None:
    """Return a filter for an object used in source code pages."""
    if isinstance(obj, Module):
        return f"__mkapi__:{obj.fullname}=0"
    if obj.module.name == module.name and obj.node:
        return f"__mkapi__:{obj.fullname}={obj.node.lineno-1}"
    return None


def _render_source(obj: Module, context: dict[str, Any], filters: list[str]) -> str:
    if source := get_source(obj):
        lines = source.splitlines()
        for filter_ in filters:
            if filter_.startswith("__mkapi__:"):
                name, index_str = filter_[10:].split("=")
                index = int(index_str)
                if len(lines[index]) > 80 and index:
                    index -= 1
                line = lines[index]
                if "## __mkapi__." not in line:
                    lines[index] = f"{line}## __mkapi__.{name}"
        source = "\n".join(lines)
    else:
        source = ""
    context["source"] = source
    return templates["source"].render(context)
