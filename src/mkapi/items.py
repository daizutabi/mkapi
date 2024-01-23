"""Element module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import is_property
from mkapi.utils import (
    get_by_name,
    get_module_node,
    get_module_path,
    iter_parent_module_names,
    join_without_first_indent,
    unique_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from inspect import _ParameterKind


TypeKind = Enum("TypeKind", ["OBJECT", "REFERENCE"])


@dataclass
class Element:
    """Element type."""

    markdown: str = field(default="", init=False)
    html: str = field(default="", init=False)


@dataclass
class Type(Element):
    """Type class."""

    expr: ast.expr | None = None
    kind: TypeKind = TypeKind.REFERENCE


@dataclass
class Text(Element):
    """Text class."""

    str: str | None = None


@dataclass
class Item:
    """Element class."""

    name: str
    type: Type
    text: Text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass(repr=False)
class Parameter(Item):
    """Parameter class for [Class][mkapi.objects.Class] or [Function]."""

    default: ast.expr | None
    kind: _ParameterKind | None


def iter_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    for arg, kind, default in mkapi.ast.iter_parameters(node):
        type_ = Type(arg.annotation)
        yield Parameter(arg.arg, type_, Text(None), default, kind)


@dataclass(repr=False)
class Raise(Item):
    """Raise class for [Class] or [Function]."""


def iter_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Raise]:
    """Yield [Raise] instances."""
    for ret in mkapi.ast.iter_raises(node):
        if type_ := ret.exc:
            if isinstance(type_, ast.Call):
                type_ = type_.func
            name = ast.unparse(type_)
            yield Raise(name, Type(type_), Text(None))


@dataclass(repr=False)
class Return(Item):
    """Return class for [Class] or [Function]."""


def iter_returns(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Return]:
    """Return a [Return] instance."""
    if node.returns:
        yield Return("", Type(node.returns), Text(None))


@dataclass(repr=False)
class Base(Item):
    """Base class for [Class]."""


def iter_bases(node: ast.ClassDef) -> Iterator[Base]:
    """Yield [Raise] instances."""
    for base in node.bases:
        if isinstance(base, ast.Subscript):
            name = ast.unparse(base.value)
        else:
            name = ast.unparse(base)
        yield Base(name, Type(base), Text(None))


@dataclass(repr=False)
class Assign(Item):
    """Assign class for [Module] or [Class]."""

    default: ast.expr | None
    node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None


def iter_assigns(node: ast.ClassDef | ast.Module) -> Iterator[Assign]:
    """Yield [Assign] instances."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.AnnAssign | ast.Assign | ast.TypeAlias):
            attr = create_assign(child)
            if attr.name:
                yield attr
        elif isinstance(child, ast.FunctionDef) and is_property(child):
            yield create_assign_from_property(child)


def create_assign(node: ast.AnnAssign | ast.Assign | ast.TypeAlias) -> Assign:
    """Return an [Assign] instance."""
    name = mkapi.ast.get_assign_name(node) or ""
    type_ = mkapi.ast.get_assign_type(node)
    type_, text = _assign_type_text(type_, node.__doc__)
    default = None if isinstance(node, ast.TypeAlias) else node.value
    return Assign(name, type_, text, default, node)


def create_assign_from_property(node: ast.FunctionDef) -> Assign:
    """Return an [Assign] instance from a property."""
    node.__doc__ = ast.get_docstring(node)
    type_, text = _assign_type_text(node.returns, node.__doc__)
    return Assign(node.name, type_, text, None, node)


def _assign_type_text(type_: ast.expr | None, text: str | None) -> tuple[Type, Text]:
    if not text:
        return Type(type_), Text(None)
    type_doc, text = split_without_name(text, "google")
    if not type_ and type_doc:
        # ex. 'list(str)' -> 'list[str]' for ast.expr
        type_doc = type_doc.replace("(", "[").replace(")", "]")
        type_ = mkapi.ast.create_expr(type_doc)
    return Type(type_), Text(text)


def split_without_name(text: str, style: str) -> tuple[str, str]:
    """Return a tuple of (type, text) for Returns or Yields section."""
    lines = text.split("\n")
    if style == "google" and ":" in lines[0]:
        type_, text_ = lines[0].split(":", maxsplit=1)
        return type_.strip(), "\n".join([text_.strip(), *lines[1:]])
    if style == "numpy" and len(lines) > 1 and lines[1].startswith(" "):
        return lines[0], join_without_first_indent(lines[1:])
    return "", text


@dataclass(repr=False)
class Section(Item):
    """Section class of docstring."""

    items: list[Item]

    def __repr__(self) -> str:
        if not self.items:
            return f"{self.__class__.__name__}({self.name!r})"
        args = ", ".join(item.name for item in self.items)
        return f"{self.__class__.__name__}({args})"

    def __iter__(self) -> Iterator[Item]:
        return iter(self.items)

    def get(self, name: str) -> Item | None:
        """Return an [Item] instance by name."""
        return get_by_name(self.items, name)


@dataclass(repr=False)
class Parameters(Section):
    """Parameters section."""

    items: list[Parameter]


def create_parameters(items: Iterable[tuple[str, Type, Text]]) -> Parameters:
    """Return a parameters section."""
    parameters = [Parameter(*args, None, None) for args in items]
    return Parameters("Parameters", Type(None), Text(None), parameters)


@dataclass(repr=False)
class Assigns(Section):
    """Assigns section."""

    items: list[Assign]


def create_assigns(items: Iterable[tuple[str, Type, Text]]) -> Assigns:
    """Return an Assigns section."""
    assigns = [Assign(*args, None, None) for args in items]
    return Assigns("Assigns", Type(None), Text(None), assigns)


@dataclass(repr=False)
class Raises(Section):
    """Raises section."""

    items: list[Raise]


def create_raises(items: Iterable[tuple[str, Type, Text]]) -> Raises:
    """Return a raises section."""
    raises = [Raise(*args) for args in items]
    for raise_ in raises:
        raise_.type.expr = ast.Constant(raise_.name)
    return Raises("Raises", Type(None), Text(None), raises)


@dataclass(repr=False)
class Returns(Section):
    """Returns section."""

    items: list[Return]


def create_returns(name: str, text: str, style: str) -> Returns:
    """Return a returns  section."""
    type_, text_ = split_without_name(text, style)
    type_ = Type(ast.Constant(type_) if type_ else None)
    text_ = Text(text_ or None)
    returns = [Return("", type_, text_)]
    return Returns(name, Type(None), Text(None), returns)


@dataclass(repr=False)
class Bases(Section):
    """Bases section."""

    items: list[Base]


def iter_merged_items[T](items_ast: Sequence[T], items_doc: Sequence[T]) -> Iterator[T]:
    """Yield merged [Item] instances.

    `items_ast` are overwritten in-place.
    """
    for name in unique_names(items_ast, items_doc):
        item_ast, item_doc = get_by_name(items_ast, name), get_by_name(items_doc, name)
        if item_ast and not item_doc:
            yield item_ast
        elif not item_ast and item_doc:
            yield item_doc
        if isinstance(item_ast, Item) and isinstance(item_doc, Item):
            item_ast.name = item_ast.name or item_doc.name
            item_ast.type = item_ast.type if item_ast.type.expr else item_doc.type
            item_ast.text = item_ast.text if item_ast.text.str else item_doc.text
            yield item_ast
