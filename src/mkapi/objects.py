"""Object module."""
from __future__ import annotations

import ast
import importlib
import inspect
import itertools
from collections.abc import Callable as Callable_
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias

import mkapi.ast
import mkapi.docstrings
import mkapi.inspect
from mkapi import docstrings
from mkapi.docstrings import Docstring, split_item_without_name
from mkapi.globals import get_all, get_fullname
from mkapi.items import (
    Assign,
    Assigns,
    Default,
    Name,
    Parameter,
    Text,
    Type,
    iter_assigns,
    iter_bases,
    iter_parameters,
    iter_returns,
    merge_parameters,
    merge_returns,
)
from mkapi.utils import (
    cache,
    del_by_name,
    get_by_name,
    get_by_type,
    get_module_node_source,
    is_package,
    iter_parent_module_names,
    unique_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.items import Base, Raise, Return


objects: dict[str, Module | Class | Function | Attribute | None] = cache({})


@dataclass
class Named:
    name: Name
    qualname: Name = field(init=False)
    fullname: Name = field(init=False)


@dataclass
class Object(Named):
    """Object class."""

    node: ast.AST | None
    doc: Docstring
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

    def __iter__(self) -> Iterator[Name | Type | Text]:
        yield from super().__iter__()

        if self.type.expr:
            yield self.type

        if self.default.expr:
            yield self.default


def update_attributes(attrs: list[Attribute]) -> None:
    for attr in attrs:
        objects[attr.fullname.str] = attr


def create_attribute(
    assign: Assign,
    module: Module,
    parent: Class | Function | None,
) -> Attribute:
    """Return an [Attribute] instance."""
    node = assign.node
    module = module or _create_empty_module()

    if assign.node:
        if isinstance(assign.node, ast.FunctionDef | ast.AsyncFunctionDef):
            text = ast.get_docstring(assign.node)
        else:
            text = assign.node.__doc__

        doc = docstrings.parse(text)

        if doc.text.str and (lines := doc.text.str.splitlines()):  # noqa: SIM102
            if ":" in lines[0]:
                type_, lines[0] = (x.lstrip(" ").rstrip() for x in lines[0].split(":", maxsplit=1))
                doc.text.str = "\n".join(lines).strip()

                if not assign.type.expr:
                    assign.type.expr = ast.Constant(type_)

    else:
        doc = Docstring(Name("Docstring"), Type(), assign.text, [])

    name, type_, default = assign.name, assign.type, assign.default
    return Attribute(name, node, doc, module, parent, type_, default)


def iter_attributes(
    node: ast.ClassDef | ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
    module: Module,
    parent: Class | Function | None,
    self: str = "",
) -> Iterator[Attribute]:
    for child in iter_assigns(node, self):
        yield create_attribute(child, module, parent)


def merge_attributes(
    attributes: list[Attribute],
    module: Module,
    parent: Class | Function | None,
) -> None:
    """Merge attributes."""
    sections = parent.doc.sections if parent else module.doc.sections

    if section := get_by_type(sections, Assigns):
        for attr in attributes:
            _merge_attribute_docstring(attr, section)

        for item in reversed(section.items):
            attr = create_attribute(item, module, parent)
            attributes.insert(0, attr)

        index = sections.index(section)
        del sections[index]

    if module.source:
        _merge_attributes_comment(attributes, module.source)


def _merge_attribute_docstring(attr: Attribute, section: Assigns):
    if item := get_by_name(section.items, attr.name):
        if not attr.doc.text.str:
            attr.doc.text.str = item.text.str

        if not attr.type.expr:
            attr.type.expr = item.type.expr

        index = section.items.index(item)
        del section.items[index]


def _merge_attributes_comment(attrs: list[Attribute], source: str) -> None:
    lines = source.splitlines()

    for attr in attrs:
        if attr.doc.text.str or not (node := attr.node):
            continue

        line = lines[node.lineno - 1][node.end_col_offset :].strip()

        if line.startswith("#:"):
            _add_text_from_comment(attr, line[2:].strip())

        elif node.lineno > 1:
            line = lines[node.lineno - 2][node.col_offset :]
            if line.startswith("#:"):
                _add_text_from_comment(attr, line[2:].strip())


def _add_text_from_comment(attr: Attribute, text: str) -> None:
    if not text:
        return

    type_, text = split_item_without_name(text, "google")
    if not attr.type.expr:
        attr.type.expr = ast.Constant(type_)

    attr.doc.text.str = text


def union_attributes(la: list[Attribute], lb: list[Attribute]) -> Iterator[Attribute]:
    """Yield merged [Attribute] instances."""
    for name in unique_names(la, lb):
        a, b = get_by_name(la, name), get_by_name(lb, name)

        if a and not b:
            yield a

        elif not a and b:
            yield b

        elif isinstance(a, Attribute) and isinstance(b, Attribute):
            a.node = a.node if a.node else b.node
            a.type = a.type if a.type.expr else b.type
            a.doc = mkapi.docstrings.merge(a.doc, b.doc)
            yield a


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
    name = Name(node.name)

    text = ast.get_docstring(node)
    doc = docstrings.parse(text)

    module = module or _create_empty_module()

    params = list(iter_parameters(node))
    merge_parameters(doc.sections, params)

    returns = list(iter_returns(node))
    merge_returns(doc.sections, returns)

    # raises = list(iter_raises(node))
    # merge_raises(doc.sections, raises)
    raises = []

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

        for item in itertools.chain(self.bases, self.parameters, self.raises):
            yield from item


def create_class(
    node: ast.ClassDef,
    module: Module | None = None,
    parent: Class | Function | None = None,
) -> Class:
    """Return a [Class] instance."""
    name = Name(node.name)

    text = ast.get_docstring(node)
    doc = docstrings.parse(text)

    module = module or _create_empty_module()

    bases = list(iter_bases(node))

    cls = Class(name, node, doc, module, parent, bases)

    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls_ = create_class(child, module, cls)
            cls.classes.append(cls_)

        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            if mkapi.ast.is_function(child):
                func = create_function(child, module, cls)
                cls.functions.append(func)

    cls.attributes = list(iter_attributes(node, module, cls))
    merge_attributes(cls.attributes, module, cls)

    inherit_base_classes(cls)

    if mkapi.inspect.is_dataclass(cls):
        cls.parameters = list(iter_dataclass_parameters(cls))
    else:
        merge_init(cls)

    return cls


def iter_base_classes(cls: Class) -> Iterator[Class]:
    """Yield base classes."""
    for node in cls.node.bases:
        name = next(mkapi.ast.iter_identifiers(node))

        if base := get_by_name(cls.module.classes, name):
            yield base

        elif fullname := get_fullname(name, cls.module.name.str):
            base = _get_object(fullname)

            if base and isinstance(base, Class):
                yield base


base_classes: dict[str, list[Class]] = cache({})


def create_base_classes(cls: Class) -> list[Class]:
    if cls.fullname.str in base_classes:
        return base_classes[cls.fullname.str]

    bases = list(iter_base_classes(cls))

    base_classes[cls.fullname.str] = bases
    return bases


def inherit_base_classes(cls: Class) -> None:
    """Inherit objects from base classes."""
    # TODO: fix InitVar, ClassVar for dataclasses.
    bases = create_base_classes(cls)

    for name in ["attributes", "functions", "classes"]:
        members = {member.name.str: member for member in getattr(cls, name)}

        for base in bases:
            for member in getattr(base, name):
                members.setdefault(member.name.str, member)

        setattr(cls, name, list(members.values()))


def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
    """Yield [Parameter] instances a for dataclass signature."""
    if not cls.module or not (module_name := cls.module.name.str):
        raise NotImplementedError

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return

    members = dict(inspect.getmembers(module, inspect.isclass))
    obj = members[cls.name.str]

    for param in inspect.signature(obj).parameters.values():
        if attr := get_by_name(cls.attributes, param.name):
            args = (attr.name, attr.type, attr.doc.text, attr.default)
            yield Parameter(*args, param.kind)

        else:
            raise NotImplementedError


def merge_init(cls: Class):
    if not (init := get_by_name(cls.functions, "__init__")):
        return

    cls.parameters = init.parameters
    cls.raises = init.raises

    if init.parameters:
        self = init.parameters[0].name.str

        attrs = list(iter_attributes(init.node, cls.module, cls, self))
        merge_attributes(attrs, cls.module, cls)

        attrs = union_attributes(cls.attributes, attrs)
        cls.attributes = sorted(attrs, key=lambda attr: attr.node.lineno if attr.node else -1)
        update_attributes(cls.attributes)

    cls.doc = mkapi.docstrings.merge(cls.doc, init.doc)
    del_by_name(cls.functions, "__init__")


@dataclass(repr=False)
class Module(Object):
    """Module class."""

    node: ast.Module
    modules: list[Module] = field(default_factory=list, init=False)
    classes: list[Class] = field(default_factory=list, init=False)
    functions: list[Function] = field(default_factory=list, init=False)
    attributes: list[Attribute] = field(default_factory=list, init=False)
    source: str | None = None

    def __post_init__(self) -> None:
        self.fullname = self.qualname = self.name
        super().__post_init__()


def _create_empty_module() -> Module:
    doc = Docstring(Name("Docstring"), Type(), Text(), [])
    return Module(Name("__mkapi__"), ast.Module(), doc, None)


def _create_module(name: str, node: ast.Module, source: str | None = None) -> Module:
    """Return a [Module] instance from an [ast.Module] node."""
    text = ast.get_docstring(node)
    doc = docstrings.parse(text)

    module = Module(Name(name), node, doc, source)

    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            cls = create_class(child, module)
            module.classes.append(cls)

        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            if mkapi.ast.is_function(child):
                func = create_function(child, module)
                module.functions.append(func)

    module.attributes = list(iter_attributes(node, module, None))
    merge_attributes(module.attributes, module, None)

    return module


@cache
def create_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if not (node_source := get_module_node_source(name)):
        return None

    return _create_module(name, *node_source)


def _get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    """Return an [Object] instance by the fullname."""
    if fullname in objects:
        return objects[fullname]

    for name in iter_parent_module_names(fullname):
        if create_module(name) and fullname in objects:
            return objects[fullname]

    objects[fullname] = None
    return None


@cache
def load_module(name: str) -> Module | None:
    if not (module := create_module(name)):
        return None

    for name, fullname in get_all(module.name.str).items():
        obj = _get_object(fullname)

        asname = f"{module.name.str}.{name}"
        objects[asname] = obj

        # TODO: asname
        if isinstance(obj, Module):
            module.modules.append(obj)
        elif isinstance(obj, Class):
            module.classes.append(obj)
        elif isinstance(obj, Function):
            module.functions.append(obj)
        elif isinstance(obj, Attribute):
            module.attributes.append(obj)

    return module


@cache
def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    if fullname in objects:
        return objects[fullname]

    for name in iter_parent_module_names(fullname):
        if load_module(name) and fullname in objects:
            return objects[fullname]

    return None


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


def get_source(obj: Module | Class | Function | Attribute) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        return obj.source

    if not obj.node:
        return None

    if (module := obj.module) and (source := module.source):
        start, stop = obj.node.lineno - 1, obj.node.end_lineno
        lines = source.split("\n")
        return "\n".join(lines[start:stop]) + "\n"

    return None


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
