"""Renderer class."""
from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.importlib import get_source
from mkapi.inspect import get_signature
from mkapi.objects import Attribute, Class, Function, Module, iter_objects

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load templates."""
    if not path:
        path = Path(mkapi.__file__).parent / "templates"
    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
    for name in os.listdir(path):
        templates[Path(name).stem] = env.get_template(name)


def render(obj: Module | Class | Function | Attribute, filters: list[str]) -> str:
    """Return a rendered Markdown."""
    if isinstance(obj, Module) and "source" in filters:
        return render_source(obj, filters)
    context = {"obj": obj, "doc": obj.doc, "filters": filters}
    if isinstance(obj, Class | Function):
        context["signature"] = get_signature(obj).markdown
    return templates["object"].render(context)


def render_source(obj: Module, filters: list[str]) -> str:
    """Return a rendered source."""
    if not (source := get_source(obj)):
        return ""
    lines = source.splitlines()
    for f in filters:
        if f.startswith("__mkapi__:"):
            name, index_str = f[10:].split("=")
            index = int(index_str)
            lines[index] = f"{lines[index]}## __mkapi__.{name}"

    source = "\n".join(lines)
    return f"``` {{.python .mkapi-source}}\n{source.strip()}\n```"
    # obj_str = render_object(obj, filters)
    # return obj_str
    # doc_str = render_docstring(obj.doc, filters=filters)
    # members = []
    # for member in obj.classes + obj.functions:
    #     member_str = render(member, level + 1, filters)
    #     members.append(member_str)
    # return templates["node"].render(obj=obj_str, doc=doc_str, members=members)


# def render_object(obj: Object, level: int, filters: list[str]) -> str:
#     """Return a rendered HTML for Object."""
#     tag = f"h{level}" if level else "div"
#     signature = get_signature(obj) if isinstance(obj, Class | Function) else None
#     return templates["object"].render(
#         object=obj,
#         signature=signature,
#         tag=tag,
#         filters=filters,
#     )
