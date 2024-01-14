"""Element module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import is_property
from mkapi.utils import (
    get_by_name,
    iter_parent_modulenames,
    join_without_first_indent,
    unique_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
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
class Item:
    """Element class."""

    name: str
    type: Type  # noqa: A003
    text: Text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


@dataclass(repr=False)
class Parameter(Item):
    """Parameter class for [Class] or [Function]."""

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
class Import:
    """Import class for [Module]."""

    name: str
    fullname: str
    from_: str | None
    level: int

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


def _iter_imports(node: ast.Import | ast.ImportFrom) -> Iterator[Import]:
    """Yield [Import] instances."""
    for alias in node.names:
        if isinstance(node, ast.Import):
            if alias.asname:
                yield Import(alias.asname, alias.name, None, 0)
            else:
                for fullname in iter_parent_modulenames(alias.name):
                    yield Import(fullname, fullname, None, 0)
        else:
            name = alias.asname or alias.name
            from_ = f"{node.module}"
            fullname = f"{from_}.{alias.name}"
            yield Import(name, fullname, from_, node.level)


def iter_imports(node: ast.Module) -> Iterator[Import]:
    """Yield [Import] instances."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import | ast.ImportFrom):
            yield from _iter_imports(child)


@dataclass(repr=False)
class Attribute(Item):
    """Atrribute class for [Module] or [Class]."""

    default: ast.expr | None


def iter_attributes(node: ast.ClassDef | ast.Module) -> Iterator[Attribute]:
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
    return Attribute(name, type_, text, default)


def create_attribute_from_property(node: ast.FunctionDef) -> Attribute:
    """Return an [Attribute] instance from a property."""
    text = ast.get_docstring(node)
    type_, text = _attribute_type_text(node.returns, text)
    return Attribute(node.name, type_, text, None)


def _attribute_type_text(type_: ast.expr | None, text: str | None) -> tuple[Type, Text]:
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
            return f"{self.__class__.__name__}({self.name})"
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
class Attributes(Section):
    """Attributes section."""

    items: list[Attribute]


def create_attributes(items: Iterable[tuple[str, Type, Text]]) -> Attributes:
    """Return an attributes section."""
    attributes = [Attribute(*args, None) for args in items]
    return Attributes("Attributes", Type(None), Text(None), attributes)


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
