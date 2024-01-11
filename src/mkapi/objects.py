"""Object module."""
from __future__ import annotations

import ast
import importlib
import importlib.util
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import mkapi.ast
import mkapi.dataclasses
from mkapi import docstrings
from mkapi.utils import (
    del_by_name,
    get_by_name,
    iter_parent_modulenames,
    unique_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from inspect import _ParameterKind
    from typing import Self

    from mkapi.docstrings import Docstring, Item, Section


@dataclass
class Object:
    """Object base class."""

    _node: ast.AST
    name: str
    modulename: str | None = field(init=False)
    docstring: str | None

    def __post_init__(self) -> None:
        self.modulename = Module.get_modulename()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def get_module(self) -> Module | None:
        """Return a [Module] instance."""
        return load_module(self.modulename) if self.modulename else None

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source code segment."""
        if (module := self.get_module()) and (source := module.source):
            start, stop = self._node.lineno - 1, self._node.end_lineno
            return "\n".join(source.split("\n")[start:stop][:maxline])
        return None

    def unparse(self) -> str:
        """Unparse the AST node and return a string expression."""
        return ast.unparse(self._node)


@dataclass(repr=False)
class Import(Object):
    """Import class for [Module]."""

    _node: ast.Import | ast.ImportFrom
    fullname: str
    from_: str | None
    level: int


def iter_imports(node: ast.Import | ast.ImportFrom) -> Iterator[Import]:
    """Yield [Import] instances."""
    from_ = f"{node.module}" if isinstance(node, ast.ImportFrom) else None
    for alias in node.names:
        name = alias.asname or alias.name
        fullname = f"{from_}.{alias.name}" if from_ else name
        if isinstance(node, ast.Import):
            for parent in iter_parent_modulenames(fullname):
                yield Import(node, parent, None, parent, None, 0)
        else:
            yield Import(node, name, None, fullname, from_, node.level)


@dataclass(repr=False)
class Parameter(Object):
    """Parameter class for [Class] and [Function]."""

    _node: ast.arg | None
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    kind: _ParameterKind | None


def iter_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    for arg, kind, default in mkapi.ast.iter_parameters(node):
        yield Parameter(arg, arg.arg, None, arg.annotation, default, kind)


@dataclass(repr=False)
class Raise(Object):
    """Raise class for [Class] and [Function]."""

    _node: ast.Raise | None
    type: ast.expr | None  #   # noqa: A003

    def __repr__(self) -> str:
        exc = ast.unparse(self.type) if self.type else ""
        return f"{self.__class__.__name__}({exc})"


def iter_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Raise]:
    """Yield [Raise] instances."""
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc:
            yield Raise(child, "", None, child.exc)


@dataclass(repr=False)
class Return(Object):
    """Return class for [Class] and [Function]."""

    _node: ast.expr | None
    type: ast.expr | None  #   # noqa: A003


def get_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Return:
    """Return a [Return] instance."""
    return Return(node.returns, "", None, node.returns)


objects: dict[str, Attribute | Class | Function | Module | None] = {}


@dataclass(repr=False)
class Member(Object):
    """Member class for [Attribute], [Function], [Class], and [Module]."""

    qualname: str = field(init=False)
    fullname: str = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        qualname = Class.get_qualclassname()
        self.qualname = f"{qualname}.{self.name}" if qualname else self.name
        m_name = self.modulename
        self.fullname = f"{m_name}.{self.qualname}" if m_name else self.qualname
        objects[self.fullname] = self  # type:ignore


@dataclass(repr=False)
class Attribute(Member):
    """Atrribute class for [Module] and [Class]."""

    _node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    type_params: list[ast.type_param] | None


def get_attribute(node: ast.AnnAssign | ast.Assign | ast.TypeAlias) -> Attribute:
    """Return an [Attribute] instance."""
    name = mkapi.ast.get_assign_name(node) or ""
    doc = node.__doc__
    type_ = mkapi.ast.get_assign_type(node)
    doc, type_ = _get_attribute_doc_type(doc, type_)
    default = None if isinstance(node, ast.TypeAlias) else node.value
    type_params = node.type_params if isinstance(node, ast.TypeAlias) else None
    return Attribute(node, name, doc, type_, default, type_params)


def get_attribute_from_property(node: ast.FunctionDef) -> Attribute:
    """Return an [Attribute] instance from a property."""
    name = node.name
    doc = ast.get_docstring(node)
    type_ = node.returns
    doc, type_ = _get_attribute_doc_type(doc, type_)
    default = None
    type_params = node.type_params
    return Attribute(node, name, doc, type_, default, type_params)


def _get_attribute_doc_type(
    doc: str | None,
    type_: ast.expr | None,
) -> tuple[str | None, ast.expr | None]:
    if not doc:
        return doc, type_
    type_doc, doc = docstrings.split_without_name(doc, "google")
    if not type_ and type_doc:
        # ex. list(str) -> list[str]
        type_doc = type_doc.replace("(", "[").replace(")", "]")
        type_ = mkapi.ast.get_expr(type_doc)
    return doc, type_


@dataclass(repr=False)
class Callable(Member):
    """Callable class for [Class] and [Function]."""

    _node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    docstring: Docstring | None
    parameters: list[Parameter]
    raises: list[Raise]
    decorators: list[ast.expr]
    type_params: list[ast.type_param]

    def __iter__(self) -> Iterator[Parameter | Raise]:
        """Yield member instances."""
        yield from self.parameters
        yield from self.raises

    def get(self, name: str) -> Parameter | Raise | None:
        """Return a member instance by the name."""
        return get_by_name(self, name)

    def get_parameter(self, name: str) -> Parameter | None:
        """Return a [Parameter] instance by the name."""
        return get_by_name(self.parameters, name)

    def get_raise(self, name: str) -> Raise | None:
        """Return a [Riase] instance by the name."""
        return get_by_name(self.raises, name)


@dataclass(repr=False)
class Function(Callable):
    """Function class."""

    _node: ast.FunctionDef | ast.AsyncFunctionDef
    returns: Return

    def __iter__(self) -> Iterator[Parameter | Raise | Return]:
        """Yield member instances."""
        yield from super().__iter__()
        yield self.returns


@dataclass(repr=False)
class Class(Callable):
    """Class class."""

    _node: ast.ClassDef
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]
    bases: list[Class]
    classnames: ClassVar[list[str | None]] = [None]

    def __iter__(self) -> Iterator[Parameter | Attribute | Class | Function | Raise]:
        """Yield member instances."""
        yield from super().__iter__()
        yield from self.attributes
        yield from self.classes
        yield from self.functions

    def add_member(self, member: Attribute | Class | Function | Import) -> None:
        """Add a member."""
        if isinstance(member, Attribute):
            self.attributes.append(member)
        elif isinstance(member, Class):
            self.classes.append(member)
        elif isinstance(member, Function):
            self.functions.append(member)

    def get_attribute(self, name: str) -> Attribute | None:
        """Return an [Attribute] instance by the name."""
        return get_by_name(self.attributes, name)

    def get_class(self, name: str) -> Class | None:
        """Return a [Class] instance by the name."""
        return get_by_name(self.classes, name)

    def get_function(self, name: str) -> Function | None:
        """Return a [Function] instance by the name."""
        return get_by_name(self.functions, name)

    def iter_bases(self) -> Iterator[Class]:
        """Yield base classes including self."""
        for base in self.bases:
            yield from base.iter_bases()
        yield self

    @classmethod
    @contextmanager
    def create(cls, node: ast.ClassDef) -> Iterator[Self]:
        """Create a [Class] instance."""
        name = node.name
        args = (name, None, *_callable_args(node))
        klass = cls(node, *args, [], [], [], [])
        qualname = f"{cls.classnames[-1]}.{name}" if cls.classnames[-1] else name
        cls.classnames.append(qualname)
        yield klass
        cls.classnames.pop()

    @classmethod
    def get_qualclassname(cls) -> str | None:
        """Return current qualified class name."""
        return cls.classnames[-1]


def _callable_args(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[list[Parameter], list[Raise], list[ast.expr], list[ast.type_param]]:
    parameters = [] if isinstance(node, ast.ClassDef) else list(iter_parameters(node))
    raises = [] if isinstance(node, ast.ClassDef) else list(iter_raises(node))
    return parameters, raises, node.decorator_list, node.type_params


def get_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Function:
    """Return a [Function] instance."""
    args = (node.name, None, *_callable_args(node))
    return Function(node, *args, get_return(node))


def get_class(node: ast.ClassDef) -> Class:
    """Return a [Class] instance."""
    with Class.create(node) as cls:
        for member in iter_members(node):
            cls.add_member(member)
    return cls


def iter_members(
    node: ast.ClassDef | ast.Module,
) -> Iterator[Import | Attribute | Class | Function]:
    """Yield members."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef):  # noqa: SIM102
            if mkapi.ast.is_property(child.decorator_list):
                yield get_attribute_from_property(child)
                continue
        if isinstance(child, ast.Import | ast.ImportFrom):
            yield from iter_imports(child)
        elif isinstance(child, ast.AnnAssign | ast.Assign | ast.TypeAlias):
            attr = get_attribute(child)
            if attr.name:
                yield attr
        elif isinstance(child, ast.ClassDef):
            yield get_class(child)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            yield get_function(child)


@dataclass(repr=False)
class Module(Member):
    """Module class."""

    _node: ast.Module
    docstring: Docstring | None
    imports: list[Import]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]
    source: str | None
    kind: str | None
    modulenames: ClassVar[list[str | None]] = [None]

    def __post_init__(self) -> None:
        super().__post_init__()
        self.qualname = self.fullname = self.name
        modules[self.name] = self

    def __iter__(self) -> Iterator[Import | Attribute | Class | Function]:
        """Yield member instances."""
        yield from self.imports
        yield from self.attributes
        yield from self.classes
        yield from self.functions

    def add_member(self, member: Import | Attribute | Class | Function) -> None:
        """Add member instance."""
        if isinstance(member, Import):
            if member.level:
                prefix = ".".join(self.name.split(".")[: member.level])
                member.fullname = f"{prefix}.{member.fullname}"
            self.imports.append(member)
        elif isinstance(member, Attribute):
            self.attributes.append(member)
        elif isinstance(member, Class):
            self.classes.append(member)
        elif isinstance(member, Function):
            self.functions.append(member)

    def get(self, name: str) -> Import | Attribute | Class | Function | None:
        """Return a member instance by the name."""
        return get_by_name(self, name)

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

    def get_fullname(self, name: str | None = None) -> str | None:
        """Return the fullname of the module."""
        if not name:
            return self.name
        if obj := self.get(name):
            return obj.fullname
        if "." in name:
            name, attr = name.rsplit(".", maxsplit=1)
            if import_ := self.get_import(name):  # noqa: SIM102
                if module := load_module(import_.fullname):
                    return module.get_fullname(attr)
        return None

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source of the module."""
        if not self.source:
            return None
        return "\n".join(self.source.split("\n")[:maxline])

    @classmethod
    @contextmanager
    def create(cls, node: ast.Module, name: str) -> Iterator[Self]:  # noqa: D102
        module = cls(node, name, None, [], [], [], [], None, None)
        cls.modulenames.append(name)
        yield module
        cls.modulenames.pop()

    @classmethod
    def get_modulename(cls) -> str | None:  # noqa: D102
        return cls.modulenames[-1]


def get_module_path(name: str) -> Path | None:
    """Return the source path of the module name."""
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError:
        return None
    if not spec or not hasattr(spec, "origin") or not spec.origin:
        return None
    path = Path(spec.origin)
    if not path.exists():  # for builtin, frozen
        return None
    return path


modules: dict[str, Module | None] = {}


def load_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if name in modules:
        return modules[name]
    if not (path := get_module_path(name)):
        modules[name] = None
        return None
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    module = load_module_from_source(source, name)
    module.kind = "package" if path.stem == "__init__" else "module"
    return module


def load_module_from_source(source: str, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from source string."""
    node = ast.parse(source)
    module = load_module_from_node(node, name)
    module.source = source
    return module


def load_module_from_node(node: ast.Module, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from the [ast.Module] node."""
    with Module.create(node, name) as module:
        for member in iter_members(node):
            module.add_member(member)
        _postprocess(module)
    return module


def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    """Return a [Object] instance by the fullname."""
    if fullname in objects:
        return objects[fullname]
    for modulename in iter_parent_modulenames(fullname):
        if load_module(modulename) and fullname in objects:
            return objects[fullname]
    objects[fullname] = None
    return None


def _merge_item(obj: Attribute | Parameter | Return | Raise, item: Item) -> None:
    if not obj.type and item.type:
        # ex. list(str) -> list[str]
        type_ = item.type.replace("(", "[").replace(")", "]")
        obj.type = mkapi.ast.get_expr(type_)
    obj.docstring = item.text  # Does item.text win?


def _new(
    cls: type[Attribute | Parameter | Raise],
    name: str,
) -> Attribute | Parameter | Raise:
    if cls is Attribute:
        return Attribute(None, name, None, None, None, [])
    if cls is Parameter:
        return Parameter(None, name, None, None, None, None)
    if cls is Raise:
        return Raise(None, name, None, None)
    raise NotImplementedError


def _merge_items(cls: type, attrs: list, items: list[Item]) -> list:
    names = unique_names(attrs, items)
    attrs_ = []
    for name in names:
        if not (attr := get_by_name(attrs, name)):
            attr = _new(cls, name)
        attrs_.append(attr)
        if not (item := get_by_name(items, name)):
            continue
        _merge_item(attr, item)  # type: ignore
    return attrs_


def _merge_docstring(obj: Module | Class | Function) -> None:
    """Merge [Object] and [Docstring]."""
    if not (doc := ast.get_docstring(obj._node)):  # noqa: SLF001
        return
    sections: list[Section] = []
    docstring = docstrings.parse(doc)
    for section in docstring:
        if section.name == "Attributes" and isinstance(obj, Module | Class):
            obj.attributes = _merge_items(Attribute, obj.attributes, section.items)
        elif section.name == "Parameters" and isinstance(obj, Class | Function):
            obj.parameters = _merge_items(Parameter, obj.parameters, section.items)
        elif section.name == "Raises" and isinstance(obj, Class | Function):
            obj.raises = _merge_items(Raise, obj.raises, section.items)
        elif section.name in ["Returns", "Yields"] and isinstance(obj, Function):
            _merge_item(obj.returns, section)
            obj.returns.name = section.name
        else:
            sections.append(section)
    docstring.sections = sections
    obj.docstring = docstring


def _postprocess(obj: Module | Class) -> None:
    _merge_docstring(obj)
    for func in obj.functions:
        _merge_docstring(func)
    for cls in obj.classes:
        _postprocess(cls)
        _postprocess_class(cls)


ATTRIBUTE_ORDER_DICT = {
    ast.AnnAssign: 1,
    ast.Assign: 2,
    ast.FunctionDef: 3,
    ast.TypeAlias: 4,
}


def _attribute_order(attr: Attribute) -> int:
    if not (node := attr._node):  # noqa: SLF001
        return 0
    return ATTRIBUTE_ORDER_DICT.get(type(node), 10)


def _iter_base_classes(cls: Class) -> Iterator[Class]:
    """Yield base classes.

    This function is called in postprocess for setting base classes.
    """
    if not (module := cls.get_module()):
        return
    for node in cls._node.bases:
        base_name = next(mkapi.ast.iter_identifiers(node))
        base_fullname = module.get_fullname(base_name)
        if not base_fullname:
            continue
        base = get_object(base_fullname)
        if base and isinstance(base, Class):
            yield base


def _inherit(cls: Class, name: str) -> None:
    members = {}
    for base in cls.bases:
        for member in getattr(base, name):
            members[member.name] = member
    for member in getattr(cls, name):
        members[member.name] = member
    setattr(cls, name, list(members.values()))


def _postprocess_class(cls: Class) -> None:
    cls.bases = list(_iter_base_classes(cls))
    for name in ["attributes", "functions", "classes"]:
        _inherit(cls, name)
    if init := cls.get_function("__init__"):
        cls.parameters = init.parameters
        cls.raises = init.raises
        cls.docstring = docstrings.merge(cls.docstring, init.docstring)
        cls.attributes.sort(key=_attribute_order)
        del_by_name(cls.functions, "__init__")
    if mkapi.dataclasses.is_dataclass(cls):
        for attr, kind in mkapi.dataclasses.iter_parameters(cls):
            args = (None, attr.name, attr.docstring, attr.type, attr.default, kind)
            parameter = Parameter(*args)
            parameter.modulename = attr.modulename
            cls.parameters.append(parameter)
