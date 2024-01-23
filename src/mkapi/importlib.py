"""importlib module."""
from __future__ import annotations

import importlib
import inspect
import re
from functools import partial
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
from mkapi.ast import iter_identifiers
from mkapi.items import Parameter, TypeKind
from mkapi.objects import (
    Class,
    Module,
    create_module,
    iter_objects,
    merge_items,
    objects,
)
from mkapi.utils import (
    del_by_name,
    get_by_name,
    get_module_node_source,
    iter_parent_module_names,
)

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

    from mkapi.items import Text, Type
    from mkapi.objects import Attribute, Function

modules: dict[str, Module | None] = {}


def load_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if name in modules:
        return modules[name]
    if not (node_source := get_module_node_source(name)):
        modules[name] = None
        return None
    node, source = node_source
    module = create_module(node, name)
    module.source = source
    modules[name] = module
    _postprocess(module)
    return module


def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    """Return an [Object] instance by the fullname."""
    if fullname in modules:
        return modules[fullname]
    if fullname in objects:
        return objects[fullname]
    for module_name in iter_parent_module_names(fullname):
        if load_module(module_name) and fullname in objects:
            return objects[fullname]
    objects[fullname] = None
    return None


def get_source(
    obj: Module | Class | Function,
    maxline: int | None = None,
) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        if obj.source:
            return "\n".join(obj.source.split("\n")[:maxline])
        return None
    if (module := obj.module) and (source := module.source):
        start, stop = obj.node.lineno - 1, obj.node.end_lineno
        return "\n".join(source.split("\n")[start:stop][:maxline])
    return None


def _postprocess(obj: Module | Class) -> None:
    if isinstance(obj, Module):
        merge_items(obj)
        set_markdown(obj)
    if isinstance(obj, Class):
        _postprocess_class(obj)
    for cls in obj.classes:
        _postprocess(cls)


def _postprocess_class(cls: Class) -> None:
    inherit_base_classes(cls)
    if init := get_by_name(cls.functions, "__init__"):
        cls.parameters = init.parameters
        cls.raises = init.raises
        cls.doc = mkapi.docstrings.merge(cls.doc, init.doc)
        del_by_name(cls.functions, "__init__")
    if is_dataclass(cls):
        cls.parameters = list(iter_dataclass_parameters(cls))


def iter_base_classes(cls: Class) -> Iterator[Class]:
    """Yield base classes.

    This function is called in postprocess for inheritance.
    """
    if not cls.module:
        return
    for node in cls.node.bases:
        name = next(mkapi.ast.iter_identifiers(node))
        if fullname := get_fullname(cls.module, name):
            base = get_object(fullname)
            if base and isinstance(base, Class):
                yield base


def inherit_base_classes(cls: Class) -> None:
    """Inherit objects from base classes."""
    # TODO: fix InitVar, ClassVar for dataclasses.
    bases = list(iter_base_classes(cls))
    for name in ["attributes", "functions", "classes"]:
        members = {}
        for base in bases:
            for member in getattr(base, name):
                members[member.name] = member
        for member in getattr(cls, name):
            members[member.name] = member
        setattr(cls, name, list(members.values()))


def get_decorator(obj: Class | Function, name: str) -> ast.expr | None:
    """Return a decorator expr by name."""
    if not obj.module:
        return None
    for deco in obj.node.decorator_list:
        deco_name = next(iter_identifiers(deco))
        if get_fullname(obj.module, deco_name) == name:
            return deco
    return None


def is_dataclass(cls: Class) -> bool:
    """Return True if a [Class] instance is a dataclass."""
    return get_decorator(cls, "dataclasses.dataclass") is not None


def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
    """Yield [Parameter] instances a for dataclass signature."""
    if not cls.module or not (module_name := cls.module.name):
        raise NotImplementedError
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return
    members = dict(inspect.getmembers(module, inspect.isclass))
    obj = members[cls.name]

    for param in inspect.signature(obj).parameters.values():
        if attr := get_by_name(cls.attributes, param.name):
            args = (attr.name, attr.type, attr.text, attr.default)
            yield Parameter(*args, param.kind)
        else:
            raise NotImplementedError


# def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
#     for child in ast.iter_child_nodes(deco):
#         if isinstance(child, ast.keyword):
#             if child.arg and isinstance(child.value, ast.Constant):
#                 yield child.arg, child.value.value


# def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
#     return dict(_iter_decorator_args(deco))


LINK_PATTERN = re.compile(r"(?<!\])\[([^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


def set_markdown(module: Module) -> None:  # noqa: C901
    """Set markdown with link form."""
    cache: dict[str, str] = {}

    def _get_link_type(name: str, asname: str) -> str:
        if name in cache:
            return cache[name]
        fullname = get_fullname(module, name)
        link = f"[{asname}][__mkapi__.{fullname}]" if fullname else asname
        cache[name] = link
        return link

    def get_link_type(name: str, kind: TypeKind = TypeKind.REFERENCE) -> str:
        names = []
        parents = iter_parent_module_names(name)
        asnames = name.split(".")
        for k, (name_, asname) in enumerate(zip(parents, asnames, strict=True)):
            if kind is TypeKind.OBJECT and k == len(asnames) - 1:
                names.append(asname)
            else:
                names.append(_get_link_type(name_, asname))
        return ".".join(names)

    def get_link_text(match: re.Match) -> str:
        name = match.group(1)
        link = get_link_type(name)
        if name != link:
            return link
        return match.group()

    for type_ in _iter_types(module):
        if type_.expr:
            get_link = partial(get_link_type, kind=type_.kind)
            type_.markdown = mkapi.ast.unparse(type_.expr, get_link)

    for text in _iter_texts(module):
        if text.str:
            text.markdown = re.sub(LINK_PATTERN, get_link_text, text.str)


def _iter_types(module: Module) -> Iterator[Type]:
    for obj_ in iter_objects(module):
        yield from obj_.doc.iter_types()


def _iter_texts(module: Module) -> Iterator[Text]:
    for obj_ in iter_objects(module):
        yield from obj_.doc.iter_texts()
