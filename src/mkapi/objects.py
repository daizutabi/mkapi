"""Object module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi import docstrings
from mkapi.docstrings import Docstring
from mkapi.items import (
    Attributes,
    Bases,
    Item,
    Parameters,
    Raises,
    Returns,
    Text,
    Type,
    create_attributes,
    create_parameters,
    create_raises,
    iter_attributes,
    iter_bases,
    iter_imports,
    iter_merged_items,
    iter_parameters,
    iter_raises,
    iter_returns,
)
from mkapi.utils import get_by_name, get_by_type

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.items import Attribute, Base, Import, Parameter, Raise, Return


@dataclass
class Object:
    """Object class for class or function."""

    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    name: str
    module: Module
    parent: Object | None
    doc: Docstring
    classes: list[Class]
    functions: list[Function]
    parameters: list[Parameter]
    raises: list[Raise]
    qualname: str = field(init=False)
    fullname: str = field(init=False)

    def __post_init__(self) -> None:
        if self.parent:
            self.qualname = f"{self.parent.qualname}.{self.name}"
        else:
            self.qualname = self.name
        self.fullname = f"{self.module.name}.{self.qualname}"
        self.doc.name = self.fullname
        expr = ast.parse(self.fullname).body[0]
        if isinstance(expr, ast.Expr):
            self.doc.type.expr = expr.value
        objects[self.fullname] = self  # type:ignore

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source code segment."""
        if (module := self.module) and (source := module.source):
            start, stop = self.node.lineno - 1, self.node.end_lineno
            return "\n".join(source.split("\n")[start:stop][:maxline])
        return None

    def get_class(self, name: str) -> Class | None:
        """Return a [Class] instance by the name."""
        return get_by_name(self.classes, name)

    def get_function(self, name: str) -> Function | None:
        """Return a [Function] instance by the name."""
        return get_by_name(self.functions, name)

    def get_parameter(self, name: str) -> Parameter | None:
        """Return a [Parameter] instance by the name."""
        return get_by_name(self.parameters, name)

    def get_raise(self, name: str) -> Raise | None:
        """Return a [Raise] instance by the name."""
        return get_by_name(self.raises, name)


objects: dict[str, Class | Function | None] = {}


@dataclass(repr=False)
class Function(Object):
    """Function class."""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    returns: list[Return]


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: Module | None = None,
    parent: Object | None = None,
) -> Function:
    """Return a [Function] instance."""
    module = module or _create_empty_module()
    doc = docstrings.parse(ast.get_docstring(node))
    parameters = list(iter_parameters(node))
    raises = list(iter_raises(node))
    returns = list(iter_returns(node))
    args = ([], [], parameters, raises, returns)
    func = Function(node, node.name, module, parent, doc, *args)
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            func.classes.append(create_class(child, module, func))
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            func.functions.append(create_function(child, module, func))
    return func


@dataclass(repr=False)
class Class(Object):
    """Class class."""

    node: ast.ClassDef
    attributes: list[Attribute]
    bases: list[Base]

    def get_attribute(self, name: str) -> Attribute | None:
        """Return an [Attribute] instance by the name."""
        return get_by_name(self.attributes, name)


def create_class(
    node: ast.ClassDef,
    module: Module | None = None,
    parent: Object | None = None,
) -> Class:
    """Return a [Class] instance."""
    name = node.name
    module = module or _create_empty_module()
    doc = docstrings.parse(ast.get_docstring(node))
    attributes = list(iter_attributes(node))
    bases = list(iter_bases(node))
    args = ([], [], [], [], attributes, bases)
    cls = Class(node, name, module, parent, doc, *args)
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls.classes.append(create_class(child, module, cls))
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):  # noqa: SIM102
            if not cls.get_attribute(child.name):  # for property
                cls.functions.append(create_function(child, module, cls))
    return cls


@dataclass
class Module:
    """Module class."""

    node: ast.Module | None
    name: str
    doc: Docstring
    imports: list[Import]
    attributes: list[Attribute]
    classes: list[Class] = field(default_factory=list, init=False)
    functions: list[Function] = field(default_factory=list, init=False)
    source: str | None = None
    kind: str | None = None

    def __post_init__(self) -> None:
        expr = ast.parse(self.name).body[0]
        if isinstance(expr, ast.Expr):
            self.doc.type.expr = expr.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def get_import(self, name: str) -> Import | None:
        """Return an [Import] instance by the name."""
        return get_by_name(self.imports, name)

    def get_attribute(self, name: str) -> Attribute | None:
        """Return an [Attribute] instance by the name."""
        return get_by_name(self.attributes, name)

    def get_class(self, name: str) -> Class | None:
        """Return an [Class] instance by the name."""
        return get_by_name(self.classes, name)

    def get_function(self, name: str) -> Function | None:
        """Return an [Function] instance by the name."""
        return get_by_name(self.functions, name)

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source of the module."""
        if not self.source:
            return None
        return "\n".join(self.source.split("\n")[:maxline])

    def get_member(self, name: str) -> Import | Class | Function | None:
        """Return a member instance by the name."""
        if obj := self.get_import(name):
            return obj
        if obj := self.get_class(name):
            return obj
        if obj := self.get_function(name):
            return obj
        return None


def create_module(node: ast.Module, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from an [ast.Module] node."""
    doc = docstrings.parse(ast.get_docstring(node))
    imports = []
    for import_ in iter_imports(node):
        if import_.level:
            names = name.split(".")
            prefix = ".".join(name.split(".")[: len(names) - import_.level + 1])
            import_.fullname = f"{prefix}.{import_.fullname}"
        imports.append(import_)
    attributes = list(iter_attributes(node))
    module = Module(node, name, doc, imports, attributes, None, None)
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            module.classes.append(create_class(child, module))
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            module.functions.append(create_function(child, module))
    return module


def _create_empty_module() -> Module:
    name = "__mkapi__"
    doc = Docstring("", Type(None), Text(None), [])
    return Module(None, name, doc, [], [], None, None)


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
    section = get_by_type(obj.doc.sections, Attributes)
    if not section:
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
        section = Returns("Returns", Type(None), Text(None), [])
        obj.doc.sections.append(section)
    section.items = list(iter_merged_items(obj.returns, section.items))


def merge_bases(obj: Class) -> None:
    """Merge bases."""
    if not obj.bases:
        return
    section = Bases("Bases", Type(None), Text(None), obj.bases)
    obj.doc.sections.insert(0, section)


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


def merge_items(obj: Module | Class | Function) -> None:
    """Merge items."""
    for obj_ in iter_objects(obj):
        _merge_items(obj_)


def iter_objects(obj: Module | Class | Function) -> Iterator[Module | Class | Function]:
    """Yield [Class] or [Function] instances."""
    yield obj
    for cls in obj.classes:
        if isinstance(obj, Module) or cls.module is obj.module:
            yield from iter_objects(cls)
    for func in obj.functions:
        if isinstance(obj, Module) or func.module is obj.module:
            yield from iter_objects(func)


def iter_items(obj: Module | Class | Function) -> Iterator[Item]:
    """Yield [Item] instances."""
    for obj_ in iter_objects(obj):
        yield from obj_.doc


def iter_types(obj: Module | Class | Function) -> Iterator[Type]:
    """Yield [Type] instances."""
    for obj_ in iter_objects(obj):
        yield from obj_.doc.iter_types()


def iter_texts(obj: Module | Class | Function) -> Iterator[Text]:
    """Yield [Text] instances."""
    for obj_ in iter_objects(obj):
        yield from obj_.doc.iter_texts()
