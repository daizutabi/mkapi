"""Object module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
from mkapi import docstrings
from mkapi.docstrings import Docstring
from mkapi.items import (
    Assign,
    Assigns,
    Bases,
    Default,
    Parameters,
    Raises,
    Returns,
    Text,
    Type,
    TypeKind,
    create_attributes,
    create_parameters,
    create_raises,
    iter_assigns,
    iter_bases,
    iter_merged_items,
    iter_parameters,
    iter_raises,
    iter_returns,
)
from mkapi.utils import get_by_name, get_by_type, is_package

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.items import Base, Parameter, Raise, Return
    from mkapi.objects import Attribute, Function


objects: dict[str, Module | Class | Function | Attribute | None] = {}


@dataclass
class Object:
    """Object class."""

    name: str
    node: ast.AST | None
    doc: Docstring
    qualname: str = field(init=False)
    fullname: str = field(init=False)

    def __post_init__(self) -> None:
        self.doc.name = self.fullname
        expr = ast.parse(self.fullname).body[0]
        if isinstance(expr, ast.Expr):
            self.doc.type.expr = expr.value
            self.doc.type.kind = TypeKind.OBJECT
        objects[self.fullname] = self  # type:ignore

    def __repr__(self) -> str:
        return f"{self.kind.title()}({self.name!r})"

    @property
    def kind(self) -> str:
        """Return the kind."""
        return self.__class__.__name__.lower()


@dataclass(repr=False)
class Member(Object):
    """Member class."""

    module: Module
    parent: Callable | None

    def __post_init__(self) -> None:
        if self.parent:
            self.qualname = f"{self.parent.qualname}.{self.name}"
        else:
            self.qualname = self.name
        self.fullname = f"{self.module.name}.{self.qualname}"
        super().__post_init__()


@dataclass(repr=False)
class Attribute(Member):
    """Attribute class."""

    type: Type
    default: Default
    text: Text = field(default_factory=Text, init=False)

    def __iter__(self) -> Iterator[Type | Text]:
        if self.type.expr:
            yield self.type
        if self.default.expr:
            yield self.default

    @property
    def kind(self) -> str:
        """Return the kind."""
        return "property" if isinstance(self.node, ast.FunctionDef) else "attribute"


def create_attribute(
    assign: Assign,
    module: Module | None = None,
    parent: Class | None = None,
) -> Attribute:
    """Return an [Attribute] instance."""
    node, name = assign.node, assign.name
    type_, default = assign.type, assign.default
    module = module or _create_empty_module()
    if assign.node and assign.node.__doc__:
        doc = docstrings.parse(assign.node.__doc__)
    else:
        doc = Docstring("", Type(), Text(), [])
    return Attribute(name, node, doc, module, parent, type_, default)


@dataclass(repr=False)
class Callable(Member):
    """Callable class for class or function."""

    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    classes: list[Class] = field(default_factory=list, init=False)
    functions: list[Function] = field(default_factory=list, init=False)


@dataclass(repr=False)
class Function(Callable):
    """Function class."""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    parameters: list[Parameter]
    returns: list[Return]
    raises: list[Raise]

    @property
    def kind(self) -> str:
        """Return the kind."""
        return "method" if "." in self.qualname else "function"


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: Module | None = None,
    parent: Callable | None = None,
) -> Function:
    """Return a [Function] instance."""
    module = module or _create_empty_module()
    doc = docstrings.parse(ast.get_docstring(node))
    parameters = list(iter_parameters(node))
    raises = list(iter_raises(node))
    returns = list(iter_returns(node))
    func = Function(node.name, node, doc, module, parent, parameters, returns, raises)  # type: ignore
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            func.classes.append(create_class(child, module, func))
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            func.functions.append(create_function(child, module, func))
    return func


@dataclass(repr=False)
class Class(Callable):
    """Class class."""

    node: ast.ClassDef
    bases: list[Base]
    attributes: list[Attribute] = field(default_factory=list, init=False)
    parameters: list[Parameter] = field(default_factory=list, init=False)
    raises: list[Raise] = field(default_factory=list, init=False)


def create_class(
    node: ast.ClassDef,
    module: Module | None = None,
    parent: Callable | None = None,
) -> Class:
    """Return a [Class] instance."""
    name = node.name
    module = module or _create_empty_module()
    doc = docstrings.parse(ast.get_docstring(node))
    bases = list(iter_bases(node))
    cls = Class(name, node, doc, module, parent, bases)
    for child in iter_assigns(node):
        cls.attributes.append(create_attribute(child, module, cls))
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls.classes.append(create_class(child, module, cls))
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):  # noqa: SIM102
            if not get_by_name(cls.attributes, child.name):  # for property
                cls.functions.append(create_function(child, module, cls))
    return cls


@dataclass(repr=False)
class Module(Object):
    """Module class."""

    node: ast.Module
    attributes: list[Attribute] = field(default_factory=list, init=False)
    classes: list[Class] = field(default_factory=list, init=False)
    functions: list[Function] = field(default_factory=list, init=False)
    source: str | None = None

    def __post_init__(self) -> None:
        self.fullname = self.qualname = self.name
        super().__post_init__()

    @property
    def kind(self) -> str:
        """Return the kind: package or module."""
        return "package" if is_package(self.name) else "module"


def _create_empty_module() -> Module:
    name = "__mkapi__"
    doc = Docstring("Docstring", Type(), Text(), [])
    return Module(name, ast.Module(), doc, None)


def create_module(name: str, node: ast.Module, source: str | None = None) -> Module:
    """Return a [Module] instance from an [ast.Module] node."""
    doc = docstrings.parse(ast.get_docstring(node))
    module = Module(name, node, doc, source)
    for child in iter_assigns(node):
        module.attributes.append(create_attribute(child, module))
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            module.classes.append(create_class(child, module))
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            module.functions.append(create_function(child, module))
    merge_items(module)
    set_markdown(module)
    return module


def merge_items(module: Module) -> None:
    """Merge items."""
    for obj in iter_objects(module):
        if isinstance(obj, Module | Class | Function):
            _merge_items(obj)


def _merge_items(obj: Module | Class | Function) -> None:
    if isinstance(obj, Function | Class):
        merge_parameters(obj)
        merge_raises(obj)
    if isinstance(obj, Function):
        merge_returns(obj)
    if isinstance(obj, Module | Class):
        merge_attributes(obj)
    if isinstance(obj, Class):
        merge_bases(obj)


def set_markdown(module: Module) -> None:
    """Set markdown text with link."""
    for obj in iter_objects(module):
        obj.doc.set_markdown(module.name)


def merge_parameters(obj: Class | Function) -> None:
    """Merge parameters."""
    section = get_by_type(obj.doc.sections, Parameters)
    if not section:
        if not obj.parameters:
            return
        section = create_parameters([])
        obj.doc.sections.append(section)
    # TODO: *args, **kwargs
    section.items = list(iter_merged_items(obj.parameters, section.items))


def merge_attributes(obj: Module | Class) -> None:
    """Merge attributes."""
    if section := get_by_type(obj.doc.sections, Assigns):
        index = obj.doc.sections.index(section)
        module = obj if isinstance(obj, Module) else obj.module
        parent = obj if isinstance(obj, Class) else None
        attrs = (create_attribute(assign, module, parent) for assign in section.items)
        section = create_attributes(attrs)
        obj.doc.sections[index] = section
    else:
        if not obj.attributes:
            return
        section = create_attributes([])
        obj.doc.sections.append(section)
    section.items = list(iter_merged_items(obj.attributes, section.items))


def merge_raises(obj: Class | Function) -> None:
    """Merge raises."""
    section = get_by_type(obj.doc.sections, Raises)
    if not section:
        if not obj.raises:
            return
        section = create_raises([])
        obj.doc.sections.append(section)
    section.items = list(iter_merged_items(obj.raises, section.items))


def merge_returns(obj: Function) -> None:
    """Merge returns."""
    section = get_by_type(obj.doc.sections, Returns)
    if not section:
        if not obj.returns:
            return
        # TODO: yields
        section = Returns("Returns", Type(), Text(), [])
        obj.doc.sections.append(section)
    section.items = list(iter_merged_items(obj.returns, section.items))


def merge_bases(obj: Class) -> None:
    """Merge bases."""
    if not obj.bases:
        return
    section = Bases("Bases", Type(), Text(), obj.bases)
    obj.doc.sections.insert(0, section)


def iter_objects_with_depth(
    obj: Module | Class | Function | Attribute,
    maxdepth: int = -1,
    depth: int = 0,
) -> Iterator[tuple[Module | Class | Function | Attribute, int]]:
    """Yield [Object] instances and depth."""
    yield obj, depth
    if depth == maxdepth or isinstance(obj, Attribute):
        return
    if isinstance(obj, Module | Class):
        for attr in obj.attributes:
            yield attr, depth + 1
    for cls in obj.classes:
        if isinstance(obj, Module) or cls.module is obj.module:
            yield from iter_objects_with_depth(cls, maxdepth, depth + 1)
    for func in obj.functions:
        if isinstance(obj, Module) or func.module is obj.module:
            yield from iter_objects_with_depth(func, maxdepth, depth + 1)


def iter_objects(
    obj: Module | Class | Function | Attribute,
    maxdepth: int = -1,
) -> Iterator[Module | Class | Function | Attribute]:
    """Yield [Object] instances."""
    for obj_, _ in iter_objects_with_depth(obj, maxdepth, 0):
        yield obj_
