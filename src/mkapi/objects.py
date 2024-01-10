"""Object module."""
from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi import docstrings
from mkapi.utils import del_by_name, get_by_name, unique_names

if TYPE_CHECKING:
    from collections.abc import Iterator
    from inspect import _IntrospectableCallable, _ParameterKind
    from typing import Any

    from mkapi.docstrings import Docstring, Item, Section


STACK_MODULENAMES: list[str] = []
STACK_QUALNAMES: list[str | None] = [None]


def _push_modulename(modulename: str) -> None:
    STACK_MODULENAMES.append(modulename)


def _pop_modulename() -> str | None:
    return STACK_MODULENAMES.pop()


def _get_current_modulename() -> str | None:
    return STACK_MODULENAMES[-1] if STACK_MODULENAMES else None


def _push_classname(name: str | None) -> None:
    qualname = f"{STACK_QUALNAMES[-1]}.{name}" if STACK_QUALNAMES[-1] else name
    STACK_QUALNAMES.append(qualname)


def _pop_classname() -> str | None:
    return STACK_QUALNAMES.pop()


def _get_current_qualname() -> str | None:
    return STACK_QUALNAMES[-1]


@dataclass
class Object:
    """Object base class."""

    _node: ast.AST
    name: str
    modulename: str | None = field(init=False)
    docstring: str | None

    def __post_init__(self) -> None:
        modulename = _get_current_modulename()
        self.modulename = modulename

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __iter__(self) -> Iterator:
        yield from []

    def iter_exprs(self) -> Iterator[ast.expr | ast.type_param]:
        """Yield AST expressions."""
        for obj in self:
            if isinstance(obj, Object):
                yield from obj.iter_exprs()
            else:
                yield obj

    def get_modulename(self) -> str | None:
        """Return the module name."""
        return self.modulename

    def get_module(self) -> Module | None:
        """Return a [Module] instance."""
        if modulename := self.get_modulename():
            return get_module(modulename)
        return None

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source code segment."""
        if not (module := self.get_module()) or not (source := module.source):
            return None
        start, stop = self._node.lineno - 1, self._node.end_lineno
        return "\n".join(source.split("\n")[start:stop][:maxline])

    def unparse(self) -> str:
        """Unparse the AST node and return a string expression."""
        return ast.unparse(self._node)


@dataclass(repr=False)
class Import(Object):
    """Import class for [Module]."""

    _node: ast.Import | ast.ImportFrom
    fullname: str
    from_: str | None


def iter_imports(node: ast.Module) -> Iterator[Import]:
    """Yield import nodes and names."""
    for child in mkapi.ast.iter_import_nodes(node):
        from_ = f"{child.module}" if isinstance(child, ast.ImportFrom) else None
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_}.{alias.name}" if from_ else name
            yield Import(child, name, None, fullname, from_)


@dataclass(repr=False)
class Parameter(Object):
    """Parameter class for [Class] and [Function]."""

    _node: ast.arg | None
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    kind: _ParameterKind | None

    def __iter__(self) -> Iterator[ast.expr]:
        for expr in [self.type, self.default]:
            if expr:
                yield expr


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

    def __iter__(self) -> Iterator[ast.expr]:
        if self.type:
            yield self.type


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

    def __iter__(self) -> Iterator[ast.expr]:
        if self.type:
            yield self.type


def get_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Return:
    """Return a [Return] instance."""
    return Return(node.returns, "", None, node.returns)


CACHE_OBJECT: dict[str, Attribute | Class | Function | Module | None] = {}


@dataclass(repr=False)
class Member(Object):
    """Member class for [Attribute], [Function], [Class], and [Module]."""

    qualname: str = field(init=False)
    fullname: str = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        qualname = _get_current_qualname()
        self.qualname = f"{qualname}.{self.name}" if qualname else self.name
        m_name = self.modulename
        self.fullname = f"{m_name}.{self.qualname}" if m_name else self.qualname
        CACHE_OBJECT[self.fullname] = self  # type:ignore


@dataclass(repr=False)
class Attribute(Member):
    """Atrribute class for [Module] and [Class]."""

    _node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    type_params: list[ast.type_param] | None

    def __iter__(self) -> Iterator[ast.expr | ast.type_param]:
        for expr in [self.type, self.default]:
            if expr:
                yield expr
        if self.type_params:
            yield from self.type_params


def iter_attributes(node: ast.Module | ast.ClassDef) -> Iterator[Attribute]:
    """Yield assign nodes from the Module or Class AST node."""
    for assign in mkapi.ast.iter_assign_nodes(node):
        if not (name := mkapi.ast.get_assign_name(assign)):
            continue
        type_ = mkapi.ast.get_assign_type(assign)
        value = None if isinstance(assign, ast.TypeAlias) else assign.value
        type_params = assign.type_params if isinstance(assign, ast.TypeAlias) else None
        yield Attribute(assign, name, assign.__doc__, type_, value, type_params)


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

    def get_node_docstring(self) -> str | None:
        """Return the docstring of the node."""
        return ast.get_docstring(self._node)


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

    def __iter__(self) -> Iterator[Parameter | Attribute | Class | Function | Raise]:
        """Yield member instances."""
        yield from super().__iter__()
        yield from self.attributes
        yield from self.classes
        yield from self.functions

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


def _get_callable_args(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[list[Parameter], list[Raise], list[ast.expr], list[ast.type_param]]:
    parameters = [] if isinstance(node, ast.ClassDef) else list(iter_parameters(node))
    raises = [] if isinstance(node, ast.ClassDef) else list(iter_raises(node))
    return parameters, raises, node.decorator_list, node.type_params


def get_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Function:
    """Return a [Class] or [Function] instancd."""
    args = (node.name, None, *_get_callable_args(node))
    return Function(node, *args, get_return(node))


def get_class(node: ast.ClassDef) -> Class:
    """Return a [Class] instance."""
    _push_classname(node.name)
    args = (node.name, None, *_get_callable_args(node))
    attrs = list(iter_attributes(node))
    classes, functions = get_callables(node)
    bases: list[Class] = []
    _pop_classname()
    return Class(node, *args, attrs, classes, functions, bases)


def iter_callables(node: ast.Module | ast.ClassDef) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for child in mkapi.ast.iter_callable_nodes(node):
        if isinstance(child, ast.ClassDef):
            yield get_class(child)
        else:
            yield get_function(child)


def get_callables(
    node: ast.Module | ast.ClassDef,
) -> tuple[list[Class], list[Function]]:
    """Return a tuple of (list[Class], list[Function])."""
    classes, functions = [], []
    for callable_node in iter_callables(node):
        if isinstance(callable_node, Class):
            classes.append(callable_node)
        else:
            functions.append(callable_node)
    return classes, functions


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

    def __post_init__(self) -> None:
        super().__post_init__()
        self.qualname = self.fullname = self.name
        modules[self.name] = self

    def get_fullname(self, name: str | None = None) -> str | None:
        """Return the fullname of the module.

        If the name is given, the fullname of member is returned,
        possibly with an attribute.
        """
        if not name:
            return self.name
        if obj := self.get(name):
            return obj.fullname
        if "." in name:
            name, attr = name.rsplit(".", maxsplit=1)
            if obj := self.get(name):
                return f"{obj.fullname}.{attr}"
        return None

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source of the module."""
        if not self.source:
            return None
        return "\n".join(self.source.split("\n")[:maxline])

    def get_node_docstring(self) -> str | None:
        """Return the docstring of the node."""
        return ast.get_docstring(self._node)

    def __iter__(self) -> Iterator[Import | Attribute | Class | Function]:
        """Yield member instances."""
        yield from self.imports
        yield from self.attributes
        yield from self.classes
        yield from self.functions

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


def get_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if name in modules:
        return modules[name]
    if not (path := get_module_path(name)):
        modules[name] = None
        return None
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    module = get_module_from_source(source, name)
    module.kind = "package" if path.stem == "__init__" else "module"
    return module


def get_module_from_source(source: str, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from source string."""
    node = ast.parse(source)
    module = get_module_from_node(node, name)
    module.source = source
    return module


def get_module_from_node(node: ast.Module, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from the [ast.Module] node."""
    _push_modulename(name)
    imports = list(iter_imports(node))
    attrs = list(iter_attributes(node))
    classes, functions = get_callables(node)
    module = Module(node, name, None, imports, attrs, classes, functions, None, None)
    _postprocess_module(module)
    _postprocess(module)
    _pop_modulename()
    return module


def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    """Return a [Object] instance by the fullname."""
    if fullname in modules:
        return modules[fullname]
    if fullname in CACHE_OBJECT:
        return CACHE_OBJECT[fullname]
    names = fullname.split(".")
    for k in range(1, len(names) + 1):
        modulename = ".".join(names[:k])
        if get_module(modulename) and fullname in CACHE_OBJECT:
            return CACHE_OBJECT[fullname]
    CACHE_OBJECT[fullname] = None
    return None


def _split_attribute_docstring(obj: Attribute) -> None:
    if doc := obj.docstring:
        type_, desc = docstrings.split_without_name(doc, "google")
        if not obj.type and type_:
            # ex. list(str) -> list[str]
            type_ = type_.replace("(", "[").replace(")", "]")
            obj.type = mkapi.ast.get_expr(type_)
        obj.docstring = desc


def _move_property(obj: Class) -> None:
    funcs: list[Function] = []
    for func in obj.functions:
        node = func._node  # noqa: SLF001
        if isinstance(node, ast.AsyncFunctionDef) or not mkapi.ast.is_property(
            func.decorators,
        ):
            funcs.append(func)
            continue
        doc = func.get_node_docstring()
        type_ = func.returns.type
        type_params = func.type_params
        attr = Attribute(node, func.name, doc, type_, None, type_params)
        _split_attribute_docstring(attr)
        obj.attributes.append(attr)
    obj.functions = funcs


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
    if not (doc := obj.get_node_docstring()):
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
    for attr in obj.attributes:
        _split_attribute_docstring(attr)
    for func in obj.functions:
        _merge_docstring(func)
    for cls in obj.classes:
        _move_property(cls)
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


def _postprocess_class(cls: Class) -> None:
    cls.bases = list(_iter_base_classes(cls))
    if init := cls.get_function("__init__"):
        cls.parameters = init.parameters
        cls.raises = init.raises
        cls.docstring = docstrings.merge(cls.docstring, init.docstring)
        cls.attributes.sort(key=_attribute_order)
        del_by_name(cls.functions, "__init__")
    # TODO: dataclass


def _get_function_from_callable(obj: _IntrospectableCallable) -> Function:
    pass
    # node = mkapi.ast.get_node_from_callable(obj)
    # return get_function(node)


def _set_parameters_from_object(obj: Module | Class, members: dict[str, Any]) -> None:
    for cls in obj.classes:
        cls_obj = members[cls.name]
        if callable(cls_obj):
            func = _get_function_from_callable(cls_obj)
            cls.parameters = func.parameters
        # _set_parameters_from_object(cls, dict(inspect.getmembers(cls_obj)))
    # if isinstance(obj, Class):
    #     for func in obj.functions:
    #         f = _get_function_from_object(members[func.name])
    #         func.parameters = f.parameters


def _postprocess_module(module: Module) -> None:
    return
    module_obj = importlib.import_module(obj.name)
    members = dict(inspect.getmembers(module_obj))
    _set_parameters_from_object(obj, members)
