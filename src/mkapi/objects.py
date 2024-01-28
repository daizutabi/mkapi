"""Object module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
import mkapi.inspect
from mkapi import docstrings
from mkapi.docstrings import Docstring
from mkapi.globals import _iter_identifiers, _resolve_with_attribute, get_fullname
from mkapi.items import (
    Admonition,
    Assign,
    Assigns,
    Bases,
    Default,
    Parameters,
    Raises,
    Returns,
    SeeAlso,
    Text,
    Type,
    TypeKind,
    create_attributes,
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
    kind: str = field(init=False)

    def __post_init__(self) -> None:
        self.doc.name = self.fullname
        expr = ast.parse(self.fullname).body[0]
        if isinstance(expr, ast.Expr):
            self.doc.type.expr = expr.value
            self.doc.type.kind = TypeKind.OBJECT
        self.kind = get_kind(self)
        objects[self.fullname] = self  # type:ignore

    def __repr__(self) -> str:
        return f"{self.kind.title()}({self.name!r})"


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
        _set_markdown(obj)
        obj.doc.set_markdown(module.name)


def _set_markdown(obj: Module | Class | Function | Attribute) -> None:
    items: list[Attribute | Parameter | Return] = []
    for section in obj.doc.sections:
        if isinstance(section, Admonition):
            _set_str_admonition(section, obj)
    if isinstance(obj, Module | Class):
        items.extend(obj.attributes)
    if isinstance(obj, Class | Function):
        items.extend(obj.parameters)
    if isinstance(obj, Function):
        items.extend(obj.returns)
    module = obj.name if isinstance(obj, Module) else obj.module.name
    for item in items:
        for elem in item:
            elem.set_markdown(module)


def _set_str_admonition(
    section: Admonition,
    obj: Module | Class | Function | Attribute,
) -> None:
    if not (text := section.text.str):
        return
    if isinstance(section, SeeAlso):
        text = _add_link(obj, text)
    lines = ["    " + line if line else "" for line in text.split("\n")]
    lines.insert(0, f'!!! {section.kind} "{section.name}"')
    section.text.str = "\n".join(lines)


def _add_link(obj: Module | Class | Function | Attribute, text: str) -> str:
    strs = []
    for name, isidentifier in _iter_identifiers(text):
        if isidentifier and (fullname := _get_fullname_from_object(obj, name)):
            strs.append(f"[{name}][{fullname}]")
        else:
            strs.append(name)
    return "".join(strs)


def _get_fullname_from_object(
    obj: Module | Class | Function | Attribute,
    name: str,
) -> str | None:
    for child in iter_objects(obj, maxdepth=1):
        if child.name == name:
            return child.fullname
    if isinstance(obj, Module):
        return get_fullname(obj.name, name)
    if obj.parent and isinstance(obj.parent, Class | Function):
        return _get_fullname_from_object(obj.parent, name)
    return _resolve_with_attribute(name)


def merge_parameters(obj: Class | Function) -> None:
    """Merge parameters."""
    if not (section := get_by_type(obj.doc.sections, Parameters)):
        return
    for param_doc in section.items:
        name = param_doc.name.replace("*", "")
        if param_ast := get_by_name(obj.parameters, name):
            if not param_doc.type.expr:
                param_doc.type = param_ast.type
            if not param_doc.default.expr:
                param_doc.default = param_ast.default
            param_doc.kind = param_ast.kind


def merge_attributes(obj: Module | Class) -> None:
    """Merge attributes."""
    if not (section := get_by_type(obj.doc.sections, Assigns)):
        return
    index = obj.doc.sections.index(section)
    module = obj if isinstance(obj, Module) else obj.module
    parent = obj if isinstance(obj, Class) else None
    attrs = (create_attribute(assign, module, parent) for assign in section.items)
    section = create_attributes(attrs)
    obj.doc.sections[index] = section
    for attr_doc in section.items:
        if attr_ast := get_by_name(obj.attributes, attr_doc.name):
            if not attr_doc.type.expr:
                attr_doc.type = attr_ast.type
            if not attr_doc.default.expr:
                attr_doc.default = attr_ast.default


def merge_raises(obj: Class | Function) -> None:
    """Merge raises."""
    section = get_by_type(obj.doc.sections, Raises)
    if not section:
        if not obj.raises:
            return
        section = create_raises([])
        obj.doc.sections.append(section)
    section.items = list(iter_merged_items(obj.raises, section.items))
    for item in section.items:
        item.name = ""


def merge_returns(obj: Function) -> None:
    """Merge returns."""
    if section := get_by_type(obj.doc.sections, Returns):
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


def get_kind(obj: Object) -> str:  # noqa: PLR0911
    """Return object kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"
    if isinstance(obj, Class):
        return "dataclass" if mkapi.inspect.is_dataclass(obj) else "class"
    if isinstance(obj, Function):
        if mkapi.inspect.is_classmethod(obj):
            return "classmethod"
        if mkapi.inspect.is_staticmethod(obj):
            return "staticmethod"
        return "method" if "." in obj.qualname else "function"
    if isinstance(obj, Attribute):
        return "property" if isinstance(obj.node, ast.FunctionDef) else "attribute"
    return "unknown"


def is_empty(obj: Object) -> bool:
    """Return True if a [Object] instance is empty."""
    if not docstrings.is_empty(obj.doc):
        return False
    if isinstance(obj, Attribute):
        return True
    if isinstance(obj, Function) and obj.name.startswith("_"):
        return True
    return False
