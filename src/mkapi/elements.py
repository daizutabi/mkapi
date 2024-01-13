"""Element module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.dataclasses
from mkapi.ast import is_property
from mkapi.utils import iter_parent_modulenames

if TYPE_CHECKING:
    from collections.abc import Iterator
    from inspect import _ParameterKind


@dataclass
class Type:
    """Type class."""

    expr: ast.expr | None = None
    markdown: str = field(default="", init=False)


@dataclass
class Text:
    """Text class."""

    str: str | None = None  # noqa: A003
    markdown: str = field(default="", init=False)


@dataclass
class Element:
    """Element class."""

    name: str
    node: ast.AST | None
    type: Type  # noqa: A003
    text: Text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


@dataclass(repr=False)
class Parameter(Element):
    """Parameter class for [Class] or [Function]."""

    node: ast.arg | None
    default: ast.expr | None
    kind: _ParameterKind | None


def create_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    for arg, kind, default in mkapi.ast.iter_parameters(node):
        type_ = Type(arg.annotation)
        yield Parameter(arg.arg, arg, type_, Text(None), default, kind)


@dataclass(repr=False)
class Raise(Element):
    """Raise class for [Class] or [Function]."""

    node: ast.Raise | None


def create_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Raise]:
    """Yield [Raise] instances."""
    for ret in mkapi.ast.iter_raises(node):
        if type_ := ret.exc:
            if isinstance(type_, ast.Call):
                type_ = type_.func
            name = ast.unparse(type_)
            yield Raise(name, ret, Type(type_), Text(None))


@dataclass(repr=False)
class Return(Element):
    """Return class for [Class] or [Function]."""

    node: ast.expr | None


def create_returns(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Return]:
    """Return a [Return] instance."""
    if node.returns:
        yield Return("", node.returns, Type(node.returns), Text(None))


@dataclass(repr=False)
class Base(Element):
    """Base class for [Class]."""

    node: ast.expr | None


def create_bases(node: ast.ClassDef) -> Iterator[Base]:
    """Yield [Raise] instances."""
    for base in node.bases:
        if isinstance(base, ast.Subscript):
            name = ast.unparse(base.value)
        else:
            name = ast.unparse(base)
        yield Base(name, base, Type(base), Text(None))


@dataclass(repr=False)
class Import:
    """Import class for [Module]."""

    node: ast.Import | ast.ImportFrom
    name: str
    fullname: str
    from_: str | None
    level: int

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


def _create_imports(node: ast.Import | ast.ImportFrom) -> Iterator[Import]:
    """Yield [Import] instances."""
    for alias in node.names:
        if isinstance(node, ast.Import):
            if alias.asname:
                yield Import(node, alias.asname, alias.name, None, 0)
            else:
                for fullname in iter_parent_modulenames(alias.name):
                    yield Import(node, fullname, fullname, None, 0)
        else:
            name = alias.asname or alias.name
            from_ = f"{node.module}"
            fullname = f"{from_}.{alias.name}"
            yield Import(node, name, fullname, from_, node.level)


def create_imports(node: ast.Module) -> Iterator[Import]:
    """Yield [Import] instances."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import | ast.ImportFrom):
            yield from _create_imports(child)


@dataclass(repr=False)
class Attribute(Element):
    """Atrribute class for [Module] or [Class]."""

    node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None
    default: ast.expr | None


def create_attributes(node: ast.ClassDef | ast.Module) -> Iterator[Attribute]:
    """Yield [Attribute] instances."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.AnnAssign | ast.Assign | ast.TypeAlias):
            attr = create_attribute(child)
            if attr.name:
                yield attr
        elif isinstance(child, ast.FunctionDef) and is_property(child):
            yield create_attribute_from_property(child)


def create_attribute(node: ast.AnnAssign | ast.Assign | ast.TypeAlias) -> Attribute:
    """Return an [Attribute] instance."""
    name = mkapi.ast.get_assign_name(node) or ""
    type_ = mkapi.ast.get_assign_type(node)
    type_, text = _attribute_type_text(type_, node.__doc__)
    default = None if isinstance(node, ast.TypeAlias) else node.value
    return Attribute(name, node, type_, text, default)


def create_attribute_from_property(node: ast.FunctionDef) -> Attribute:
    """Return an [Attribute] instance from a property."""
    text = ast.get_docstring(node)
    type_, text = _attribute_type_text(node.returns, text)
    return Attribute(node.name, node, type_, text, None)


def _attribute_type_text(type_: ast.expr | None, text: str | None) -> tuple[Type, Text]:
    if not text:
        return Type(type_), Text(None)
    type_doc, text = _split_without_name(text)
    if not type_ and type_doc:
        # ex. 'list(str)' -> 'list[str]' for ast.expr
        type_doc = type_doc.replace("(", "[").replace(")", "]")
        type_ = mkapi.ast.create_expr(type_doc)
    return Type(type_), Text(text)


def _split_without_name(text: str) -> tuple[str, str]:
    """Return a tuple of (type, text) for Returns or Yields section."""
    lines = text.split("\n")
    if ":" in lines[0]:
        type_, text_ = lines[0].split(":", maxsplit=1)
        return type_.strip(), "\n".join([text_.strip(), *lines[1:]])
    return "", text
