"""AST module."""
from __future__ import annotations

import ast
import re
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    ImportFrom,
    Name,
    TypeAlias,
)
from dataclasses import dataclass, field
from importlib.util import find_spec
from inspect import Parameter as P  # noqa: N817
from inspect import cleandoc
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi import docstrings
from mkapi.utils import del_by_name, get_by_name, is_package, unique_names

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator
    from inspect import _ParameterKind

    from mkapi.docstrings import Docstring, Item, Section, Style

type Import_ = ast.Import | ImportFrom
type FunctionDef_ = AsyncFunctionDef | FunctionDef
type Def = FunctionDef_ | ClassDef
type Assign_ = Assign | AnnAssign | TypeAlias

CURRENT_MODULE_NAME: list[str | None] = [None]


@dataclass
class Object:  # noqa: D101
    _node: AST
    name: str
    docstring: str | None

    def __post_init__(self) -> None:  # Set parent module name.
        self.__dict__["__module_name__"] = CURRENT_MODULE_NAME[0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def get_module_name(self) -> str | None:
        """Return the module name."""
        return self.__dict__["__module_name__"]

    def get_module(self) -> Module | None:
        """Return a [Module] instance."""
        if module_name := self.get_module_name():
            return get_module(module_name)
        return None

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source code segment."""
        if (name := self.get_module_name()) and (source := _get_module_source(name)):
            start, stop = self._node.lineno - 1, self._node.end_lineno
            return "\n".join(source.split("\n")[start:stop][:maxline])
        return None

    def unparse(self) -> str:
        """Unparse the AST node and return a string expression."""
        return ast.unparse(self._node)


@dataclass
class Import(Object):  # noqa: D101
    _node: ast.Import | ImportFrom = field(repr=False)
    docstring: str | None = field(repr=False)
    fullname: str
    from_: str | None


def iter_import_nodes(node: AST) -> Iterator[Import_]:
    """Yield import nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Import | ImportFrom):
            yield child
        elif not isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield from iter_import_nodes(child)


def iter_imports(node: ast.Module) -> Iterator[Import]:
    """Yield import nodes and names."""
    for child in iter_import_nodes(node):
        from_ = f"{child.module}" if isinstance(child, ImportFrom) else None
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_}.{alias.name}" if from_ else name
            yield Import(child, name, None, fullname, from_)


@dataclass(repr=False)
class Attribute(Object):  # noqa: D101
    _node: Assign_ | FunctionDef_ | None  # Needs FunctionDef_ for property.
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    type_params: list[ast.type_param] | None


def _get_pseudo_docstring(node: AST) -> str | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Constant):
        return None
    doc = node.value.value
    return cleandoc(doc) if isinstance(doc, str) else None


def iter_assign_nodes(node: ast.Module | ClassDef) -> Iterator[Assign_]:
    """Yield assign nodes."""
    assign_node: Assign_ | None = None
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AnnAssign | Assign | TypeAlias):
            if assign_node:
                yield assign_node
            child.__doc__ = None
            assign_node = child
        else:
            if assign_node:
                assign_node.__doc__ = _get_pseudo_docstring(child)
                yield assign_node
            assign_node = None
    if assign_node:
        assign_node.__doc__ = None
        yield assign_node


def get_assign_name(node: Assign_) -> str | None:
    """Return the name of the assign node."""
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    if isinstance(node, Assign) and isinstance(node.targets[0], Name):
        return node.targets[0].id
    if isinstance(node, TypeAlias) and isinstance(node.name, Name):
        return node.name.id
    return None


def get_type(node: Assign_) -> ast.expr | None:
    """Return a type annotation of the Assign or TypeAlias AST node."""
    if isinstance(node, AnnAssign):
        return node.annotation
    if isinstance(node, TypeAlias):
        return node.value
    return None


def iter_attributes(node: ast.Module | ClassDef) -> Iterator[Attribute]:
    """Yield assign nodes from the Module or Class AST node."""
    for assign in iter_assign_nodes(node):
        if not (name := get_assign_name(assign)):
            continue
        type_ = get_type(assign)
        value = None if isinstance(assign, TypeAlias) else assign.value
        type_params = assign.type_params if isinstance(assign, TypeAlias) else None
        attr = Attribute(assign, name, assign.__doc__, type_, value, type_params)
        _merge_attribute_docstring(attr)
        yield attr


@dataclass(repr=False)
class Parameter(Object):  # noqa: D101
    _node: ast.arg | None
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    kind: _ParameterKind | None


PARAMETER_KIND_DICT: dict[_ParameterKind, str] = {
    P.POSITIONAL_ONLY: "posonlyargs",  # before '/', list
    P.POSITIONAL_OR_KEYWORD: "args",  # normal, list
    P.VAR_POSITIONAL: "vararg",  # *args, arg or None
    P.KEYWORD_ONLY: "kwonlyargs",  # after '*' or '*args', list
    P.VAR_KEYWORD: "kwarg",  # **kwargs, arg or None
}


def _iter_parameters(node: FunctionDef_) -> Iterator[tuple[ast.arg, _ParameterKind]]:
    for kind, attr in PARAMETER_KIND_DICT.items():
        if args := getattr(node.args, attr):
            it = args if isinstance(args, list) else [args]
            yield from ((arg, kind) for arg in it)


def _iter_defaults(node: FunctionDef_) -> Iterator[ast.expr | None]:
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional
    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


def iter_parameters(node: FunctionDef_) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    it = _iter_defaults(node)
    for arg, kind in _iter_parameters(node):
        default = None if kind in [P.VAR_POSITIONAL, P.VAR_KEYWORD] else next(it)
        name = arg.arg
        if kind is P.VAR_POSITIONAL:
            name = f"*{name}"
        if kind is P.VAR_KEYWORD:
            name = f"**{name}"
        yield Parameter(arg, name, None, arg.annotation, default, kind)


@dataclass(repr=False)
class Raise(Object):  # noqa: D101
    _node: ast.Raise | None
    type: ast.expr | None  #   # noqa: A003

    def __repr__(self) -> str:
        exc = ast.unparse(self.type) if self.type else ""
        return f"{self.__class__.__name__}({exc})"


def iter_raises(node: FunctionDef_) -> Iterator[Raise]:
    """Yield [Raise] instances."""
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc:
            yield Raise(child, "", None, child.exc)


@dataclass(repr=False)
class Return(Object):  # noqa: D101
    _node: ast.expr | None
    type: ast.expr | None  #   # noqa: A003


def get_return(node: FunctionDef_) -> Return:
    """Return a [Return] instance."""
    return Return(node.returns, "", None, node.returns)


@dataclass(repr=False)
class Callable(Object):  # noqa: D101
    docstring: str | Docstring | None
    parameters: list[Parameter]
    decorators: list[ast.expr]
    type_params: list[ast.type_param]
    raises: list[Raise]
    parent: Class | None

    def get_parameter(self, name: str) -> Parameter | None:  # noqa: D102
        return get_by_name(self.parameters, name)

    def get_fullname(self, sep: str = ".") -> str:  # noqa: D102
        if self.parent:
            return f"{self.parent.get_fullname()}.{self.name}"
        module_name = self.get_module_name() or ""
        return f"{module_name}{sep}{self.name}"

    @property
    def id(self) -> str:  # noqa: D102, A003
        return self.get_fullname()


@dataclass(repr=False)
class Function(Callable):  # noqa: D101
    _node: FunctionDef_
    returns: Return


type ClassMember = Parameter | Attribute | Class | Function


@dataclass(repr=False)
class Class(Callable):  # noqa: D101
    _node: ClassDef
    bases: list[Class]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]

    def get_attribute(self, name: str) -> Attribute | None:  # noqa: D102
        return get_by_name(self.attributes, name)

    def get_class(self, name: str) -> Class | None:  # noqa: D102
        return get_by_name(self.classes, name)

    def get_function(self, name: str) -> Function | None:  # noqa: D102
        return get_by_name(self.functions, name)

    def get(self, name: str) -> ClassMember | None:  # noqa: D102
        if obj := self.get_parameter(name):
            return obj
        if obj := self.get_attribute(name):
            return obj
        if obj := self.get_class(name):
            return obj
        if obj := self.get_function(name):
            return obj
        return None


def iter_callable_nodes(node: ast.Module | ClassDef) -> Iterator[Def]:
    """Yield callable nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield child


def _get_callable_args(
    node: Def,
) -> tuple[
    str,
    str | None,
    list[Parameter],
    list[ast.expr],
    list[ast.type_param],
    list[Raise],
]:
    name = node.name
    docstring = ast.get_docstring(node)
    parameters = [] if isinstance(node, ClassDef) else list(iter_parameters(node))
    decorators = node.decorator_list

    type_params = node.type_params
    raises = [] if isinstance(node, ClassDef) else list(iter_raises(node))
    return name, docstring, parameters, decorators, type_params, raises


def _set_parent(obj: Class) -> None:
    for cls in obj.classes:
        cls.parent = obj
    for func in obj.functions:
        func.parent = obj


def iter_callables(node: ast.Module | ClassDef) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for def_node in iter_callable_nodes(node):
        args = _get_callable_args(def_node)
        if isinstance(def_node, ClassDef):
            attrs = list(iter_attributes(def_node))
            classes, functions = get_callables(def_node)
            bases: list[Class] = []
            cls = Class(def_node, *args, None, bases, attrs, classes, functions)
            _set_parent(cls)
            _move_property(cls)
            yield cls
        else:
            yield Function(def_node, *args, None, get_return(def_node))


def get_callables(node: ast.Module | ClassDef) -> tuple[list[Class], list[Function]]:
    """Return a tuple of (list[Class], list[Function])."""
    classes: list[Class] = []
    functions: list[Function] = []
    for callable_ in iter_callables(node):
        if isinstance(callable_, Class):
            classes.append(callable_)
        else:
            functions.append(callable_)
    return classes, functions


type ModuleMember = Import | Attribute | Class | Function


@dataclass(repr=False)
class Module(Object):  # noqa: D101
    docstring: str | Docstring | None
    imports: list[Import]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]
    source: str
    kind: str

    def get_import(self, name: str) -> Import | None:  # noqa: D102
        return get_by_name(self.imports, name)

    def get_attribute(self, name: str) -> Attribute | None:  # noqa: D102
        return get_by_name(self.attributes, name)

    def get_class(self, name: str) -> Class | None:  # noqa: D102
        return get_by_name(self.classes, name)

    def get_function(self, name: str) -> Function | None:  # noqa: D102
        return get_by_name(self.functions, name)

    def get(self, name: str) -> ModuleMember | None:  # noqa: D102
        if obj := self.get_import(name):
            return obj
        if obj := self.get_attribute(name):
            return obj
        if obj := self.get_class(name):
            return obj
        if obj := self.get_function(name):
            return obj
        return None

    def get_source(self) -> str:
        """Return the source code."""
        return _get_module_source(self.name) if self.name else ""


CACHE_MODULE_NODE: dict[str, tuple[float, ast.Module | None, str]] = {}
CACHE_MODULE: dict[str, Module | None] = {}


def _get_module_node(name: str) -> ast.Module | None:
    """Return a [ast.Module] node by the name."""
    try:
        spec = find_spec(name)
    except ModuleNotFoundError:
        return None
    if not spec or not spec.origin:
        return None
    path = Path(spec.origin)
    if not path.exists():  # for builtin, frozen
        return None
    mtime = path.stat().st_mtime
    if name in CACHE_MODULE_NODE and mtime == CACHE_MODULE_NODE[name][0]:
        return CACHE_MODULE_NODE[name][1]
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    CACHE_MODULE_NODE[name] = (mtime, node, source)
    if name in CACHE_MODULE:
        del CACHE_MODULE[name]
    return node


def _get_module_source(name: str) -> str:
    if name in CACHE_MODULE_NODE:
        return CACHE_MODULE_NODE[name][2]
    return ""


def _get_module_from_node(node: ast.Module) -> Module:
    """Return a [Module] instance from the [ast.Module] node."""
    docstring = ast.get_docstring(node)
    imports = list(iter_imports(node))
    attrs = list(iter_attributes(node))
    classes, functions = get_callables(node)
    return Module(node, "", docstring, imports, attrs, classes, functions, "", "")


def get_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if name in CACHE_MODULE:  # TODO: reload
        return CACHE_MODULE[name]
    if node := _get_module_node(name):
        CURRENT_MODULE_NAME[0] = name  # Set the module name in a global cache.
        module = _get_module_from_node(node)
        CURRENT_MODULE_NAME[0] = None  # Remove the module name from a global cache.
        module.name = name
        module.source = _get_module_source(name)  # Set from a global cache.
        module.kind = "package" if is_package(name) else "module"
        _postprocess(module)
        CACHE_MODULE[name] = module
        return module
    CACHE_MODULE[name] = None
    return None


def get_object_from_module(name: str, module: Module) -> Module | ModuleMember | None:
    """Return a [Object] instance by the name from a [Module] instance."""
    obj = module.get(name)
    if isinstance(obj, Import):
        return get_object(obj.fullname)
    return obj


def get_object(fullname: str) -> Module | ModuleMember | None:
    """Return a [Object] instance by the fullname."""
    if module := get_module(fullname):
        return module
    if "." not in fullname:
        return None
    module_name, name = fullname.rsplit(".", maxsplit=1)
    if not (module := get_module(module_name)):
        return None
    return get_object_from_module(name, module)


# a1.b_2(c[d]) -> a1, b_2, c, d
SPLIT_IDENTIFIER_PATTERN = re.compile(r"[\.\[\]\(\)|]|\s+")


def _split_name(name: str) -> list[str]:
    return [x for x in re.split(SPLIT_IDENTIFIER_PATTERN, name) if x]


def _is_identifier(name: str) -> bool:
    return name != "" and all(x.isidentifier() for x in _split_name(name))


def _to_expr(name: str) -> ast.expr:
    if _is_identifier(name):
        name = name.replace("(", "[").replace(")", "]")  # ex. list(str) -> list[str]
        expr = ast.parse(name).body[0]
        if isinstance(expr, ast.Expr):
            return expr.value
    return Constant(value=name)


def _merge_attribute_docstring(obj: Attribute) -> None:
    if doc := obj.docstring:
        type_, desc = docstrings.split_without_name(doc, "google")
        if not obj.type and type_:
            obj.type = _to_expr(type_)
        obj.docstring = desc


def _is_property(obj: Function) -> bool:
    return any(ast.unparse(deco).startswith("property") for deco in obj.decorators)


def _move_property(obj: Class) -> None:
    funcs: list[Function] = []
    for func in obj.functions:
        if not _is_property(func):
            funcs.append(func)
            continue
        doc = func.docstring if isinstance(func.docstring, str) else ""
        type_ = func.returns.type
        type_params = func.type_params
        attr = Attribute(func._node, func.name, doc, type_, None, type_params)  # noqa: SLF001
        _merge_attribute_docstring(attr)
        obj.attributes.append(attr)
    obj.functions = funcs


CURRENT_DOCSTRING_STYLE: list[Style] = ["google"]


def _get_style(doc: str) -> Style:
    for names in docstrings.SECTION_NAMES:
        for name in names:
            if f"\n\n{name}\n----" in doc:
                CURRENT_DOCSTRING_STYLE[0] = "numpy"
                return "numpy"
    CURRENT_DOCSTRING_STYLE[0] = "google"
    return "google"


def _merge_item(obj: Attribute | Parameter | Return | Raise, item: Item) -> None:
    if not obj.type and item.type:
        obj.type = _to_expr(item.type)
    obj.docstring = item.description  # Does item.description win?


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
    sections: list[Section] = []
    if not (doc := obj.docstring) or not isinstance(doc, str):
        return
    style = _get_style(doc)
    docstring = docstrings.parse(doc, style)
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


DEBUG_FOR_PYTEST = False  # for pytest.


def _postprocess(obj: Module | Class) -> None:
    if DEBUG_FOR_PYTEST:
        return
    for function in obj.functions:
        _merge_docstring(function)
        if isinstance(obj, Class):
            del function.parameters[0]  # Delete 'self' TODO: static method.
    for cls in obj.classes:
        _postprocess(cls)
        _postprocess_class(cls)
    _merge_docstring(obj)


_ATTRIBUTE_ORDER_DICT = {
    type(None): 0,
    AnnAssign: 1,
    Assign: 2,
    FunctionDef: 3,
    AsyncFunctionDef: 4,
}


def _attribute_order(attr: Attribute) -> int:
    return _ATTRIBUTE_ORDER_DICT.get(type(attr._node), 10)  # type: ignore  # noqa: SLF001


def _postprocess_class(cls: Class) -> None:
    if init := cls.get_function("__init__"):
        cls.parameters = init.parameters
        cls.raises = init.raises
        cls.docstring = docstrings.merge(cls.docstring, init.docstring)  # type: ignore
        cls.attributes.sort(key=_attribute_order)
        del_by_name(cls.functions, "__init__")
    # TODO: dataclass, bases
