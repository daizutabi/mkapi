"""Converter module."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from inspect import _ParameterKind as P
from typing import TYPE_CHECKING, TypeAlias

import mkapi.ast
import mkapi.markdown
import mkapi.object
from mkapi.doc import Doc, Item, Section, create_summary_item
from mkapi.node import get_fullname
from mkapi.object import (
    Attribute,
    Class,
    Function,
    Module,
    Type,
    get_fullname_from_object,
    get_object,
    get_object_kind,
)
from mkapi.utils import (
    find_item_by_name,
    is_identifier,
    iter_attribute_names,
    iter_identifiers,
    split_module_name,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.object import Parameter


@dataclass
class Name:
    id: str
    fullname: str
    names: list[str]


@dataclass
class Parser:
    name: str
    module: str | None
    obj: Attribute | Class | Function | Module

    @staticmethod
    def create(name: str) -> Parser | None:
        if not (name_module := split_module_name(name)):
            return None

        name, module = name_module
        obj = get_object(name, module)

        if not isinstance(obj, (Attribute, Class, Function, Module)):
            return None

        return Parser(name, module, obj)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self.module!r})"

    def replace_from_module(self, name: str) -> str | None:
        return get_fullname(name, self.module or self.name)

    def replace_from_object(self, name: str) -> str | None:
        return get_fullname_from_object(name, self.obj)

    def parse_name(self) -> Name:
        id_ = f"{self.module}.{self.name}" if self.module else self.name
        names = [x.replace("_", "\\_") for x in self.name.split(".")]
        fullname = get_markdown_name(id_)

        return Name(id_, fullname, names)

    def parse_signature(self) -> list[tuple[str, str]]:
        if isinstance(self.obj, Module):
            return []

        signatures = []
        for part in get_signature(self.obj):
            if isinstance(part.name, ast.expr):
                name = get_markdown_expr(part.name, self.replace_from_module)

            elif part._kind in [PartKind.ANN, PartKind.RETURN]:
                name = get_markdown_str(part.name, self.replace_from_module)

            else:
                name = part.name

            signatures.append((name, part.kind))

        return signatures

    def parse_doc(self) -> Doc:
        doc = self.obj.doc.clone()

        if isinstance(self.obj, Module | Class):
            attrs = [x for _, x in self.obj.get_children(Type)]
            merge_attributes(doc.sections, attrs)

        if isinstance(self.obj, Function | Class):
            merge_parameters(doc.sections, self.obj.parameters)
            merge_raises(doc.sections, self.obj.raises)

        if isinstance(self.obj, Function):
            merge_returns(doc.sections, self.obj.node.returns)

        doc.text = get_markdown_text(doc.text, self.replace_from_object)
        doc.type = get_markdown_type(doc.type, self.replace_from_object)

        for section in doc.sections:
            section.text = get_markdown_text(section.text, self.replace_from_object)
            section.type = get_markdown_type(section.type, self.replace_from_object)

            for item in section.items:
                item.text = get_markdown_text(item.text, self.replace_from_object)
                item.type = get_markdown_type(item.type, self.replace_from_object)

        return doc


PREFIX = "__mkapi__."
LINK_PATTERN = re.compile(r"(?<!\])\[(?P<name>[^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


def get_markdown_link(name: str, ref: str | None, *, in_code: bool = False) -> str:
    if not in_code:
        name = name.replace("_", "\\_")

    if in_code:
        return f"[`{name}`][{PREFIX}{ref}]" if ref else f"`{name}`"

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


def get_markdown_type(type_: str | ast.expr | None, replace: Replace) -> str:
    if type_ is None:
        return ""

    if isinstance(type_, str):
        return get_markdown_str(type_, replace)

    return get_markdown_expr(type_, replace)


def get_markdown_text(text: str, replace: Replace) -> str:
    """Return markdown links from docstring text."""

    def _replace(match: re.Match) -> str:
        name = match.group("name")

        if name.startswith("`") and name.endswith("`"):
            name = name[1:-1]
            in_code = True
        else:
            in_code = False

        if name.startswith("__mkapi__."):
            from_mkapi = True
            name = name[10:]
        else:
            from_mkapi = False

        if is_identifier(name) and replace and (ref := replace(name)):
            return get_markdown_link(name, ref, in_code=in_code)

        if from_mkapi:
            return name

        return match.group()

    return mkapi.markdown.sub(LINK_PATTERN, _replace, text)


@dataclass
class Signature:
    parts: list[Part]

    def __getitem__(self, index: int) -> Part:
        return self.parts[index]

    def __len__(self) -> int:
        return len(self.parts)

    def __iter__(self) -> Iterator[Part]:
        return iter(self.parts)


@dataclass
class Part:
    name: ast.expr | str
    _kind: PartKind

    @property
    def kind(self) -> str:
        return self._kind.value


class PartKind(Enum):
    ANN = "ann"
    ARG = "arg"
    ARROW = "arrow"
    COLON = "colon"
    COMMA = "comma"
    DEFAULT = "default"
    EQUAL = "equal"
    PAREN = "paren"
    RETURN = "return"
    SLASH = "slash"
    STAR = "star"


def get_signature(obj: Class | Function | Attribute) -> Signature:
    """Return signature."""
    if isinstance(obj, Class | Function):
        parts = [Part(value, kind) for value, kind in _iter_signature(obj)]
        return Signature(parts)

    if obj.type:
        parts = [Part(": ", PartKind.COLON), Part(obj.type, PartKind.RETURN)]
        return Signature(parts)

    return Signature([])


def _iter_signature(
    obj: Class | Function,
) -> Iterator[tuple[ast.expr | str, PartKind]]:
    yield "(", PartKind.PAREN
    n = len(obj.parameters)
    prev_kind = None

    for k, param in enumerate(obj.parameters):
        if k == 0 and get_object_kind(obj) in ["class", "method", "classmethod"]:
            continue

        yield from _iter_sep(param.kind, prev_kind)

        yield param.name.replace("_", "\\_"), PartKind.ARG
        yield from _iter_param(param)

        if k < n - 1:
            yield ", ", PartKind.COMMA

        prev_kind = param.kind

    if prev_kind is P.POSITIONAL_ONLY:
        yield ", ", PartKind.COMMA
        yield "/", PartKind.SLASH

    yield ")", PartKind.PAREN

    if isinstance(obj, Class) or not obj.node.returns:
        return

    yield " → ", PartKind.ARROW
    yield obj.node.returns, PartKind.RETURN


def _iter_sep(kind: P | None, prev_kind: P | None) -> Iterator[tuple[str, PartKind]]:
    if prev_kind is P.POSITIONAL_ONLY and kind != prev_kind:
        yield "/", PartKind.SLASH
        yield ", ", PartKind.COMMA

    if kind is P.KEYWORD_ONLY and prev_kind not in [kind, P.VAR_POSITIONAL]:
        yield r"\*", PartKind.STAR
        yield ", ", PartKind.COMMA

    if kind is P.VAR_POSITIONAL:
        yield r"\*", PartKind.STAR

    if kind is P.VAR_KEYWORD:
        yield r"\*\*", PartKind.STAR


def _iter_param(param: Parameter) -> Iterator[tuple[ast.expr | str, PartKind]]:
    if param.type:
        yield ": ", PartKind.COLON
        yield param.type, PartKind.ANN

    if param.default:
        eq = " = " if param.type else "="
        yield eq, PartKind.EQUAL
        yield param.default, PartKind.DEFAULT


def merge_parameters(sections: list[Section], params: list[Parameter]) -> None:
    """Merge parameters."""
    if not (section := find_item_by_name(sections, "Parameters")):
        return

    for item in section.items:
        if item.type:
            continue

        name = item.name.replace("*", "")
        if param := find_item_by_name(params, name):
            item.type = param.type


def merge_raises(sections: list[Section], raises: list[ast.expr]) -> None:
    """Merge raises."""
    section = find_item_by_name(sections, "Raises")

    if not section:
        if not raises:
            return

        section = Section("Raises", "", "", [])
        sections.append(section)

    for raise_ in raises:
        if find_item_by_name(section.items, ast.unparse(raise_), attr="type"):
            continue

        section.items.append(Item("", raise_, ""))


def merge_returns(sections: list[Section], returns: ast.expr | None) -> None:
    """Merge returns."""
    if not (section := find_item_by_name(sections, ("Returns", "Yields"))):
        return

    if len(section.items) == 1:
        item = section.items[0]

        if not item.type and returns:
            item.type = returns


def merge_attributes(sections: list[Section], attrs: list[Type]) -> None:
    """Merge attributes."""
    if section := find_item_by_name(sections, "Attributes"):
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

        attr = find_item_by_name(attrs, item.name)
        if attr and (attr.type or attr.doc.type):
            item.type = attr.type or attr.doc.type

    for attr in attrs:
        if find_item_by_name(items, attr.name):
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
