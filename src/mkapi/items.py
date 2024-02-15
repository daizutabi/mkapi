"""Element module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from inspect import _ParameterKind
from typing import TYPE_CHECKING, TypeVar

import mkapi.ast
import mkapi.markdown
from mkapi.ast import is_property
from mkapi.utils import get_by_name, get_by_type, unique_names

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence


@dataclass
class Name:
    """Name class."""

    str: str = ""  # noqa: A003, RUF100
    markdown: str = field(default="", compare=False)

    def __repr__(self) -> str:
        name = self.str
        return f"{self.__class__.__name__}({name!r})"

    def join(self, name: Name) -> Name:
        if self.str:
            return Name(f"{self.str}.{name.str}")

        return Name(name.str)


@dataclass
class Type:
    """Type class."""

    expr: ast.expr | None = None
    markdown: str = ""

    def __repr__(self) -> str:
        type_str = ast.unparse(self.expr) if self.expr else ""
        return f"{self.__class__.__name__}({type_str})"


@dataclass(repr=False)
class Default(Type):
    """Default class."""


@dataclass
class Text:
    """Text class."""

    str: str = ""  # noqa: A003, RUF100
    markdown: str = ""

    def __repr__(self) -> str:
        text = self.str
        return f"{self.__class__.__name__}({text!r})"


@dataclass
class Item:
    """Item class."""

    name: Name
    type: Type  # noqa: A003, RUF100
    text: Text

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        type_str = ast.unparse(self.type.expr) if self.type.expr else ""
        return f"{class_name}({self.name.str}:{type_str})"

    def __iter__(self) -> Iterator[Name | Type | Text]:
        if self.name.str:
            yield self.name

        if self.type.expr:
            yield self.type

        if self.text.str:
            yield self.text


@dataclass(repr=False)
class Parameter(Item):
    """Parameter class."""

    default: Default
    kind: _ParameterKind = _ParameterKind.POSITIONAL_OR_KEYWORD

    def __iter__(self) -> Iterator[Name | Type | Text]:
        yield from super().__iter__()

        if self.default.expr:
            yield self.default


def iter_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[Parameter]:
    """Yield [Parameter] instances."""
    for arg, kind, default in mkapi.ast.iter_parameters(node):
        yield Parameter(Name(arg.arg), Type(arg.annotation), Text(), Default(default), kind)


@dataclass(repr=False)
class Assign(Item):
    """Assign class for [Module] or [Class]."""

    default: Default
    node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None


def iter_assigns(node: ast.ClassDef | ast.Module) -> Iterator[Assign]:
    """Yield [Assign] instances."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.AnnAssign | ast.Assign) or TypeAlias and isinstance(child, TypeAlias):
            attr = create_assign(child)
            if attr.name:
                yield attr

        elif isinstance(child, ast.FunctionDef) and is_property(child, read_only=True):
            yield create_assign_from_property(child)


def create_assign(node: ast.AnnAssign | ast.Assign | ast.TypeAlias) -> Assign:
    """Return an [Assign] instance."""
    name = mkapi.ast.get_assign_name(node) or ""
    type_ = mkapi.ast.get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value
    return Assign(Name(name), Type(type_), Text(), Default(default), node)


def create_assign_from_property(node: ast.FunctionDef) -> Assign:
    """Return an [Assign] instance from a property."""
    return Assign(Name(node.name), Type(node.returns), Text(), Default(), node)


@dataclass(repr=False)
class Raise(Item):
    """Raise class."""


def iter_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Raise]:
    """Yield [Raise] instances."""
    for raise_ in mkapi.ast.iter_raises(node):
        if type_ := raise_.exc:
            if isinstance(type_, ast.Call):
                type_ = type_.func
            yield Raise(Name(), Type(type_), Text())


@dataclass(repr=False)
class Return(Item):
    """Return class for [Class] or [Function]."""


def iter_returns(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Return]:
    """Yield one [Return] instance if it isn't None."""
    if node.returns:
        yield Return(Name(), Type(node.returns), Text())


@dataclass(repr=False)
class Base(Item):
    """Base class for [Class]."""


def iter_bases(node: ast.ClassDef) -> Iterator[Base]:
    """Yield [Base] instances."""
    for base in node.bases:
        yield Base(Name(), Type(base), Text())


@dataclass(repr=False)
class Section(Item):
    """Section class of docstring."""

    items: list[Item]
    kind: str | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(items={len(self.items)})"

    def __iter__(self) -> Iterator[Name | Type | Text]:
        yield from super().__iter__()

        for item in self.items:
            yield from item


@dataclass(repr=False)
class Parameters(Section):
    """Parameters section."""

    items: list[Parameter]


def create_parameters(items: Iterable[Item]) -> Parameters:
    """Return a parameters section."""
    parameters = [Parameter(item.name, item.type, item.text, Default()) for item in items]
    return Parameters(Name("Parameters"), Type(), Text(), parameters)


@dataclass(repr=False)
class Assigns(Section):
    """Assigns section."""

    items: list[Assign]


def create_assigns(items: Iterable[Item]) -> Assigns:
    """Return an Assigns section."""
    assigns = [Assign(item.name, item.type, item.text, Default(), None) for item in items]
    return Assigns(Name("Assigns"), Type(), Text(), assigns)


@dataclass(repr=False)
class Raises(Section):
    """Raises section."""

    items: list[Raise]


def create_raises(items: Iterable[Item]) -> Raises:
    """Return a [Raises] section."""
    raises = [Raise(Name(), Type(ast.Constant(item.name.str)), item.text) for item in items]
    return Raises(Name("Raises"), Type(), Text(), raises)


@dataclass(repr=False)
class Returns(Section):
    """Returns section."""

    items: list[Return]


def create_returns(items: Iterable[Item], name: str) -> Returns:
    """Return a [Returns] section."""
    returns = [Return(item.name, item.type, item.text) for item in items]
    return Returns(Name(name), Type(), Text(), returns)


@dataclass(repr=False)
class Admonition(Section):
    """Admonition section."""

    kind: str


@dataclass(repr=False)
class Notes(Admonition):
    """Notes section."""


@dataclass(repr=False)
class Warnings(Admonition):
    """Warnings section."""


@dataclass(repr=False)
class SeeAlso(Admonition):
    """SeeAlso section."""


def create_admonition(name: str, text: str) -> Admonition:
    """Create admonition."""
    if name.startswith("Note"):
        cls = Notes
        kind = "note"
    elif name.startswith("Warning"):
        cls = Warnings
        kind = "warning"
    elif name.startswith("See Also"):
        cls = SeeAlso
        kind = "info"
        text = mkapi.markdown.get_see_also(text)
    else:
        raise NotImplementedError
    text = mkapi.markdown.get_admonition(kind, name, text)
    return cls(Name(name), Type(), Text(text), [], kind)


def merge_parameters(sections: list[Section], parameters: list[Parameter]) -> None:
    """Merge parameters."""
    if not (section := get_by_type(sections, Parameters)):
        return

    for item in section.items:
        name = item.name.str.replace("*", "")

        if param := get_by_name(parameters, name):
            if not item.type.expr:
                item.type = param.type

            if not item.default.expr:
                item.default = param.default

            item.kind = param.kind


def merge_returns(sections: list[Section], returns: list[Return]) -> None:
    """Merge returns."""
    if not (section := get_by_type(sections, Returns)):
        return

    if len(returns) == 1 and len(section.items) == 1:
        item = section.items[0]

        if not item.type.expr:
            item.type = returns[0].type


def merge_raises(sections: list[Section], raises: list[Raise]) -> None:
    """Merge raises."""
    section = get_by_type(sections, Raises)

    if not section:
        if not raises:
            return

        section = create_raises([])
        sections.append(section)

    section.items = list(iter_merged_items(section.items, raises))


T = TypeVar("T")


def iter_merged_items(items_doc: Sequence[T], items_ast: Sequence[T]) -> Iterator[T]:
    """Yield merged [Item] instances."""
    for name in unique_names(items_doc, items_ast):
        item_doc, item_ast = get_by_name(items_doc, name), get_by_name(items_ast, name)
        if item_doc and not item_ast:
            yield item_doc
        elif not item_doc and item_ast:
            yield item_ast
        elif isinstance(item_doc, Item) and isinstance(item_ast, Item):
            item_doc.name = item_doc.name if item_doc.name.str else item_ast.name
            item_doc.type = item_doc.type if item_doc.type.expr else item_ast.type
            item_doc.text = item_doc.text if item_doc.text.str else item_ast.text
            yield item_doc
