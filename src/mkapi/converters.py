"""Converter module."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from inspect import _ParameterKind as P
from typing import TYPE_CHECKING, TypeAlias

import mkapi.ast
import mkapi.markdown
from mkapi.docs import Item, Section, create_summary_item, is_empty
from mkapi.nodes import get_fullname
from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Object,
    Parent,
    Type,
    get_fullname_from_object,
    get_kind,
    get_members,
    get_object,
    is_child,
)
from mkapi.utils import (
    get_by_name,
    is_identifier,
    iter_attribute_names,
    iter_identifiers,
    split_name,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from mkapi.objects import Parameter


@dataclass
class Converter:
    name: str
    module: str | None
    obj: Object
    depth: int
    fullname: str = field(init=False)

    def __post_init__(self):
        self.fullname = f"{self.module}.{self.name}" if self.module else self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self.module!r})"

    def replace_from_module(self, name: str) -> str | None:
        return get_fullname(name, self.module or self.name)

    def replace_from_object(self, name: str) -> str | None:
        return get_fullname_from_object(name, self.obj)

    def convert_name(self) -> dict[str, Any]:
        id_ = self.fullname
        names = [x.replace("_", "\\_") for x in self.name.split(".")]
        fullname = get_markdown_name(self.fullname)

        return {"id": id_, "fullname": fullname, "names": names}


def _split_name_depth(name: str) -> tuple[str, int]:
    if m := re.match(r"(.*)\.(\*+)", name):
        return m.group(1), int(len(m.group(2)))

    return name, 0


def create_converter(name: str) -> Converter | None:
    name, depth = _split_name_depth(name)

    if not (name_module := split_name(name)):
        return None

    name_, module = name_module
    if not name_:
        return None

    if not (obj := get_object(name_, module)):
        return None

    return Converter(name_, module, obj, depth)


def iter_objects(
    converter: Converter,
    predicate: Callable[[str], bool] | None = None,
) -> Iterator[tuple[str, Object, int]]:
    fullname = converter.fullname
    obj = converter.obj
    maxdepth = converter.depth

    yield fullname, obj, 0

    if not isinstance(obj, Parent) or not maxdepth:
        return

    yield from _iter_object(obj, fullname, maxdepth, predicate)


def _iter_object(
    obj: Parent,
    prefix: str,
    maxdepth: int,
    predicate: Callable[[str], bool] | None = None,
    depth: int = 1,
) -> Iterator[tuple[str, Object, int]]:
    for name, member in _get_members(obj):
        if not _predicate(member, obj):
            continue

        fullname = f"{prefix}.{name}"
        if predicate and not predicate(fullname):
            continue

        yield fullname, member, depth

        if isinstance(member, Parent) and depth < maxdepth:
            yield from _iter_object(member, fullname, maxdepth, predicate, depth + 1)


def _get_members(obj: Parent) -> Iterator[tuple[str, Object]]:
    for type_ in [Class, Function, Attribute]:
        members = get_members(obj, lambda x, type_=type_: isinstance(x, type_))
        yield from members.items()


def _predicate(obj: Object, parent: Object | None) -> bool:
    if not is_child(obj, parent):
        return False

    if is_empty(obj.doc):
        return False

    return True


PREFIX = "__mkapi__."
LINK_PATTERN = re.compile(r"(?<!\])\[(?P<name>[^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


def get_markdown_link(name: str, ref: str | None) -> str:
    name = name.replace("_", "\\_")
    return f"[{name}][{PREFIX}{ref}]" if ref else name


Replace: TypeAlias = Callable[[str], str | None] | None


def get_markdown_name(fullname: str, replace: Replace = None) -> str:
    """Return markdown links"""
    names = fullname.split(".")
    refs = iter_attribute_names(fullname)

    if replace:
        refs = [replace(ref) for ref in refs]

    it = zip(names, refs, strict=True)
    return ".".join(get_markdown_link(*names) for names in it)


def get_markdown_str(type_string: str, replace: Replace) -> str:
    """Return markdown links from string-type."""
    it = iter_identifiers(type_string)
    markdowns = (get_markdown_name(name, replace) if is_ else name for name, is_ in it)
    return "".join(markdowns)


def get_markdown_expr(expr: ast.expr, replace: Replace = None) -> str:
    """Set Markdown text with link."""
    if isinstance(expr, ast.Constant):
        value = expr.value

        if isinstance(value, str):
            return get_markdown_str(value, replace)

        return str(value)

    def get_link(name: str) -> str:
        return get_markdown_name(name, replace)

    try:
        return mkapi.ast.unparse(expr, get_link)
    except ValueError:
        return ast.unparse(expr)


def get_markdown_text(text: str, replace: Replace) -> str:
    """Return markdown links from docstring text."""

    def _replace(match: re.Match) -> str:
        name = match.group("name")

        if name.startswith("__mkapi__."):
            from_mkapi = True
            name = name[10:]
        else:
            from_mkapi = False

        if is_identifier(name) and replace and (ref := replace(name)):
            return get_markdown_link(name, ref)

        if from_mkapi:
            return name

        return match.group()

    return mkapi.markdown.sub(LINK_PATTERN, _replace, text)


def get_signature(
    obj: Class | Function | Attribute,
) -> list[tuple[ast.expr | str, str]]:
    """Return signature."""
    if isinstance(obj, Class | Function):
        return list(_iter_signature(obj))

    if obj.type:
        return [(": ", "colon"), (obj.type, "return")]

    return []


def _iter_signature(obj: Class | Function) -> Iterator[tuple[ast.expr | str, str]]:
    yield "(", "paren"
    n = len(obj.parameters)
    prev_kind = None

    for k, param in enumerate(obj.parameters):
        if k == 0 and get_kind(obj) in ["class", "method", "classmethod"]:
            continue

        yield from _iter_sep(param.kind, prev_kind)

        yield param.name.replace("_", "\\_"), "arg"
        yield from _iter_param(param)

        if k < n - 1:
            yield ", ", "comma"

        prev_kind = param.kind

    if prev_kind is P.POSITIONAL_ONLY:
        yield ", ", "comma"
        yield "/", "slash"

    yield ")", "paren"

    if isinstance(obj, Class) or not obj.node.returns:
        return

    yield " → ", "arrow"
    yield obj.node.returns, "return"


def _iter_sep(kind: P | None, prev_kind: P | None) -> Iterator[tuple[str, str]]:
    if prev_kind is P.POSITIONAL_ONLY and kind != prev_kind:
        yield "/", "slash"
        yield ", ", "comma"

    if kind is P.KEYWORD_ONLY and prev_kind not in [kind, P.VAR_POSITIONAL]:
        yield r"\*", "star"
        yield ", ", "comma"

    if kind is P.VAR_POSITIONAL:
        yield r"\*", "star"

    if kind is P.VAR_KEYWORD:
        yield r"\*\*", "star"


def _iter_param(param: Parameter) -> Iterator[tuple[ast.expr | str, str]]:
    if param.type:
        yield ": ", "colon"
        yield param.type, "ann"

    if param.default:
        eq = " = " if param.type else "="
        yield eq, "equal"
        yield param.default, "default"


def merge_parameters(sections: list[Section], params: list[Parameter]) -> None:
    """Merge parameters."""
    if not (section := get_by_name(sections, "Parameters")):
        return

    for item in section.items:
        if item.type:
            continue

        name = item.name.replace("*", "")
        if param := get_by_name(params, name):
            item.type = param.type


def merge_raises(sections: list[Section], raises: list[ast.expr]) -> None:
    """Merge raises."""
    section = get_by_name(sections, "Raises")

    if not section:
        if not raises:
            return

        section = Section("Raises", "", "", [])
        sections.append(section)

    for raise_ in raises:
        if get_by_name(section.items, ast.unparse(raise_), attr="type"):
            continue

        section.items.append(Item("", raise_, ""))


def merge_returns(sections: list[Section], returns: ast.expr | None) -> None:
    """Merge returns."""
    if not (section := get_by_name(sections, ("Returns", "Yields"))):
        return

    if len(section.items) == 1:
        item = section.items[0]

        if not item.type and returns:
            item.type = returns


def merge_attributes(sections: list[Section], attrs: list[Type]) -> None:
    """Merge attributes."""
    if section := get_by_name(sections, "Attributes"):
        items = section.items
        created = False

    else:
        if not attrs:
            return

        items = []
        section = Section("Attributes", "", "", items)
        created = True

    for item in items:
        if item.type:
            continue

        attr = get_by_name(attrs, item.name)
        if attr and (attr.type or attr.doc.type):
            item.type = attr.type or attr.doc.type

    for attr in attrs:
        if get_by_name(items, attr.name):
            continue

        type_ = attr.type or attr.doc.type
        if attr.doc.sections:
            item = create_summary_item(attr.name, attr.doc.text, type_)
            items.append(item)

        elif attr.doc.text:
            item = Item(attr.name, type_, attr.doc.text)
            items.append(item)

    if items and created:
        sections.append(section)
