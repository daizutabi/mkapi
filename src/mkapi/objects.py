"""Object module."""
from __future__ import annotations

import ast
import itertools
from collections.abc import Callable as Callable_
from dataclasses import dataclass, field
from functools import partial
from typing import TYPE_CHECKING, TypeAlias

import mkapi.ast
import mkapi.docstrings
import mkapi.inspect
from mkapi import docstrings
from mkapi.docstrings import Docstring
from mkapi.globals import get_fullname, resolve_with_attribute
from mkapi.items import (
    Assign,
    Assigns,
    Default,
    Name,
    Parameters,
    Raises,
    Returns,
    Text,
    Type,
    _assign_type_text,
    create_raises,
    iter_assigns,
    iter_bases,
    iter_merged_items,
    iter_parameters,
    iter_raises,
    iter_returns,
)
from mkapi.utils import cache, get_by_name, get_by_type, is_package

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.items import Base, Parameter, Raise, Return


objects: dict[str, Module | Class | Function | Attribute | None] = cache({})


@dataclass
class Object:
    """Object class."""

    name: Name
    node: ast.AST | None
    doc: Docstring
    qualname: Name = field(init=False)
    fullname: Name = field(init=False)
    kind: str = field(init=False)

    def __post_init__(self) -> None:
        self.kind = get_kind(self)
        objects[self.fullname.str] = self  # type:ignore

    def __iter__(self) -> Iterator[Name]:
        if self.name.str:
            yield self.name
        if self.qualname.str:
            yield self.qualname
        if self.fullname.str:
            yield self.fullname

    def __repr__(self) -> str:
        return f"{self.kind.title()}({self.name.str!r})"


@dataclass(repr=False)
class Member(Object):
    """Member class."""

    module: Module
    parent: Class | Function | None

    def __post_init__(self) -> None:
        if self.parent:
            self.qualname = self.parent.qualname.join(self.name)
        else:
            self.qualname = Name(self.name.str)
        self.fullname = self.module.name.join(self.qualname)
        super().__post_init__()


@dataclass(repr=False)
class Attribute(Member):
    """Attribute class."""

    node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None
    type: Type  # noqa: A003, RUF100
    default: Default
    text: Text = field(default_factory=Text, init=False)

    def __iter__(self) -> Iterator[Name | Type | Text]:
        yield from super().__iter__()
        if self.type.expr:
            yield self.type
        if self.default.expr:
            yield self.default
        if self.text.str:
            yield self.text


def create_attribute(
    assign: Assign,
    module: Module | None = None,
    parent: Class | None = None,
) -> Attribute:
    """Return an [Attribute] instance."""
    node = assign.node
    module = module or _create_empty_module()
    if assign.node and assign.node.__doc__:
        doc = docstrings.parse(assign.node.__doc__)
        if doc.text.str and (lines := doc.text.str.splitlines()):  # noqa: SIM102
            if ":" in lines[0]:
                _, lines[0] = lines[0].split(":", maxsplit=1)
                doc.text.str = "\n".join(lines).strip()
    else:
        doc = Docstring(Name("Docstring"), Type(), assign.text, [])
    name, type_, default = assign.name, assign.type, assign.default
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

    def __iter__(self) -> Iterator[Name | Type | Text]:
        """Yield [Type] or [Text] instances."""
        yield from super().__iter__()
        for item in itertools.chain(self.parameters, self.returns, self.raises):
            yield from item


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: Module | None = None,
    parent: Class | Function | None = None,
) -> Function:
    """Return a [Function] instance."""
    module = module or _create_empty_module()
    name = Name(node.name)
    text = ast.get_docstring(node)
    doc = docstrings.parse(text)
    params = list(iter_parameters(node))
    returns = list(iter_returns(node))
    raises = list(iter_raises(node))
    func = Function(name, node, doc, module, parent, params, returns, raises)
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls = create_class(child, module, func)
            func.classes.append(cls)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            func_ = create_function(child, module, func)
            func.functions.append(func_)
    return func


@dataclass(repr=False)
class Class(Callable):
    """Class class."""

    node: ast.ClassDef
    bases: list[Base]
    attributes: list[Attribute] = field(default_factory=list, init=False)
    parameters: list[Parameter] = field(default_factory=list, init=False)
    raises: list[Raise] = field(default_factory=list, init=False)

    def __iter__(self) -> Iterator[Name | Type | Text]:
        """Yield [Type] or [Text] instances."""
        yield from super().__iter__()
        for item in itertools.chain(self.bases, self.attributes, self.parameters, self.raises):
            yield from item


def create_class(
    node: ast.ClassDef,
    module: Module | None = None,
    parent: Class | Function | None = None,
) -> Class:
    """Return a [Class] instance."""
    name = Name(node.name)
    module = module or _create_empty_module()
    text = ast.get_docstring(node)
    doc = docstrings.parse(text)
    bases = list(iter_bases(node))
    cls = Class(name, node, doc, module, parent, bases)
    for child in iter_assigns(node):
        attr = create_attribute(child, module, cls)
        cls.attributes.append(attr)
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls_ = create_class(child, module, cls)
            cls.classes.append(cls_)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            if mkapi.ast.is_function(child):
                func = create_function(child, module, cls)
                cls.functions.append(func)
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

    def __iter__(self) -> Iterator[Name | Type | Text]:
        """Yield [Type] or [Text] instances."""
        yield from super().__iter__()
        for item in self.attributes:
            yield from item


def _create_empty_module() -> Module:
    doc = Docstring(Name("Docstring"), Type(), Text(), [])
    return Module(Name("__mkapi__"), ast.Module(), doc, None)


def create_module(name: str, node: ast.Module, source: str | None = None) -> Module:
    """Return a [Module] instance from an [ast.Module] node."""
    text = ast.get_docstring(node)
    doc = docstrings.parse(text)
    module = Module(Name(name), node, doc, source)
    for child in iter_assigns(node):
        attr = create_attribute(child, module)
        module.attributes.append(attr)
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls = create_class(child, module)
            module.classes.append(cls)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            if mkapi.ast.is_function(child):
                func = create_function(child, module)
                module.functions.append(func)
    merge_items(module)
    set_markdown(module)
    return module


def merge_items(module: Module) -> None:
    """Merge items."""
    for obj in iter_objects(module):
        if isinstance(obj, Function | Class):
            merge_parameters(obj)
            merge_raises(obj)
        if isinstance(obj, Function):
            merge_returns(obj)
        if isinstance(obj, Module | Class):
            _add_doc_comments(obj.attributes, module.source)
            merge_attributes(obj)


def _add_doc_comments(attrs: list[Attribute], source: str | None = None) -> None:
    if not source:
        return
    lines = source.splitlines()
    for attr in attrs:
        if attr.doc.text.str or not (node := attr.node):
            continue
        line = lines[node.lineno - 1][node.end_col_offset :].strip()
        if line.startswith("#:"):
            _add_doc_comment(attr, line[2:].strip())
        elif node.lineno > 1:
            line = lines[node.lineno - 2][node.col_offset :]
            if line.startswith("#:"):
                _add_doc_comment(attr, line[2:].strip())


def _add_doc_comment(attr: Attribute, text: str) -> None:
    attr.type, attr.doc.text = _assign_type_text(attr.type.expr, text)


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
        item.name = Name("")


def merge_returns(obj: Function) -> None:
    """Merge returns."""
    if section := get_by_type(obj.doc.sections, Returns):
        if len(obj.returns) == 1 and len(section.items) == 1:
            item = section.items[0]
            if not item.type.expr:
                item.type = obj.returns[0].type
            obj.returns[0].text = item.text
            obj.returns[0].name = item.name
            return
        section.items = list(iter_merged_items(obj.returns, section.items))


def merge_attributes(obj: Module | Class) -> None:
    """Merge attributes."""
    if not (section := get_by_type(obj.doc.sections, Assigns)):
        return
    section.name = Name("Attributes")
    module = obj if isinstance(obj, Module) else obj.module
    parent = obj if isinstance(obj, Class) else None
    attributes = []
    for assign in section.items:
        if not (attr := get_by_name(obj.attributes, assign.name)):
            attr = create_attribute(assign, module, parent)
        else:
            if not attr.doc.text.str:
                attr.doc.text.str = assign.text.str
            if not attr.type.expr:
                attr.type.expr = assign.type.expr
        attributes.append(attr)
    for attr in obj.attributes:
        if not get_by_name(attributes, attr.name):
            attributes.append(attr)
    obj.attributes = attributes


def set_markdown(module: Module) -> None:
    """Set markdown text with link."""
    _replace_from_module = partial(get_fullname, module=module.name.str)

    for obj in iter_objects(module):
        _replace_from_object = partial(replace_from_object, obj=obj)

        for elem in itertools.chain(obj, obj.doc):
            if isinstance(elem, Name | Type):
                elem.set_markdown(_replace_from_module)

            elif not elem.markdown:
                elem.set_markdown(_replace_from_object)


def replace_from_object(
    name: str,
    obj: Module | Class | Function | Attribute,
) -> str | None:
    """Return fullname from object."""
    for child in iter_objects(obj, maxdepth=1):
        if child.name.str == name:
            return child.fullname.str
    if isinstance(obj, Module):
        return get_fullname(name, obj.name.str)
    if obj.parent:
        return replace_from_object(name, obj.parent)
    if "." not in name:
        return replace_from_object(name, obj.module)
    parent, attr = name.rsplit(".", maxsplit=1)
    if obj.name.str == parent:
        return replace_from_object(attr, obj)
    return resolve_with_attribute(name)


Member_: TypeAlias = Module | Class | Function | Attribute
Parent: TypeAlias = Module | Class | Function | None
Predicate: TypeAlias = Callable_[[Member_, Parent], bool] | None


def is_member(
    obj: Module | Class | Function | Attribute,
    parent: Module | Class | Function | None,
) -> bool:
    """Return True if obj is a member of parent."""
    if parent is None or isinstance(obj, Module) or isinstance(parent, Module):
        return True
    if obj.parent is not parent:
        return False
    return obj.module is parent.module


def iter_objects_with_depth(
    obj: Module | Class | Function | Attribute,
    maxdepth: int = -1,
    predicate: Predicate = None,
    depth: int = 0,
) -> Iterator[tuple[Module | Class | Function | Attribute, int]]:
    """Yield [Object] instances and depth."""
    if not predicate or predicate(obj, None):
        yield obj, depth

    if depth == maxdepth or isinstance(obj, Attribute):
        return

    for child in itertools.chain(obj.classes, obj.functions):
        if not predicate or predicate(child, obj):
            yield from iter_objects_with_depth(child, maxdepth, predicate, depth + 1)

    if isinstance(obj, Module | Class):
        for attr in obj.attributes:
            if not predicate or predicate(attr, obj):
                yield attr, depth + 1


def iter_objects(
    obj: Module | Class | Function | Attribute,
    maxdepth: int = -1,
    predicate: Predicate = None,
) -> Iterator[Module | Class | Function | Attribute]:
    """Yield [Object] instances."""
    for child, _ in iter_objects_with_depth(obj, maxdepth, predicate, 0):
        yield child


def _get_kind_function(func: Function) -> str:
    if mkapi.inspect.is_classmethod(func):
        return "classmethod"
    if mkapi.inspect.is_staticmethod(func):
        return "staticmethod"
    return "method" if isinstance(func.parent, Class) else "function"


def get_kind(obj: Object) -> str:
    """Return object kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name.str) else "module"
    if isinstance(obj, Class):
        return "dataclass" if mkapi.inspect.is_dataclass(obj) else "class"
    if isinstance(obj, Function):
        return _get_kind_function(obj)
    if isinstance(obj, Attribute):
        return "property" if isinstance(obj.node, ast.FunctionDef) else "attribute"
    raise NotImplementedError


def is_empty(obj: Object) -> bool:
    """Return True if a [Object] instance is empty."""
    if not docstrings.is_empty(obj.doc):
        return False
    if isinstance(obj, Attribute):
        return True
    if isinstance(obj, Function) and obj.name.str.startswith("_"):
        return True
    return False
