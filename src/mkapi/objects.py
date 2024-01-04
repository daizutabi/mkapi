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

from mkapi.docstrings import SECTION_NAMES, parse_docstring, split_attribute
from mkapi.utils import get_by_name

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator
    from inspect import _ParameterKind

    from mkapi.docstrings import Docstring, Item, Section, Style

type Import_ = ast.Import | ImportFrom
type FunctionDef_ = AsyncFunctionDef | FunctionDef
type Def = FunctionDef_ | ClassDef
type Assign_ = Assign | AnnAssign | TypeAlias

current_module_name: list[str | None] = [None]
current_docstring_style: list[Style] = ["google"]


@dataclass
class Object:  # noqa: D101
    _node: AST
    name: str
    docstring: str | None

    def __post_init__(self) -> None:
        # Set parent module.
        self.__dict__["__module_name__"] = current_module_name[0]

    def __repr__(self) -> str:
        # fullname = self.get_fullname()
        return f"{self.__class__.__name__}({self.name})"

    def get_node(self) -> AST:  # noqa: D102
        return self._node

    def unparse(self) -> str:  # noqa: D102
        return ast.unparse(self._node)

    def get_module_name(self) -> str | None:
        """Return the module name if exist."""
        return self.__dict__["__module_name__"]

    def get_module(self) -> Module | None:
        """Return a [Module] instance if exist."""
        if module_name := self.get_module_name():
            return get_module(module_name)
        return None

    def get_source(self, maxline: int | None = None) -> str:
        """Return the source code."""
        if (name := self.get_module_name()) and (source := _get_source(name)):
            lines = source.split("\n")[self._node.lineno - 1 : self._node.end_lineno]
            if maxline:
                lines = lines[:maxline]
            return "\n".join(lines)
        return ""

    def get_fullname(self) -> str:  # noqa: D102
        if module_name := self.get_module_name():
            return f"{module_name}.{self.name}"
        return self.name


@dataclass
class Import(Object):  # noqa: D101
    _node: ast.Import | ImportFrom = field(repr=False)
    docstring: str | None = field(repr=False)
    fullname: str
    from_: str | None

    def get_fullname(self) -> str:  # noqa: D102
        return self.fullname


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
    _node: Assign_ | FunctionDef_
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
    """Return annotation."""
    if isinstance(node, AnnAssign):
        return node.annotation
    if isinstance(node, TypeAlias):
        return node.value
    return None


def iter_attributes(node: ast.Module | ClassDef) -> Iterator[Attribute]:
    """Yield assign nodes."""
    for assign in iter_assign_nodes(node):
        if not (name := get_assign_name(assign)):
            continue
        type_ = get_type(assign)
        value = None if isinstance(assign, TypeAlias) else assign.value
        type_params = assign.type_params if isinstance(assign, TypeAlias) else None
        attr = Attribute(assign, name, assign.__doc__, type_, value, type_params)
        _merge_docstring_attribute(attr)
        yield attr


@dataclass(repr=False)
class Parameter(Object):  # noqa: D101
    _node: ast.arg
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    kind: _ParameterKind


ARGS_KIND: dict[_ParameterKind, str] = {
    P.POSITIONAL_ONLY: "posonlyargs",  # before '/', list
    P.POSITIONAL_OR_KEYWORD: "args",  # normal, list
    P.VAR_POSITIONAL: "vararg",  # *args, arg or None
    P.KEYWORD_ONLY: "kwonlyargs",  # after '*' or '*args', list
    P.VAR_KEYWORD: "kwarg",  # **kwargs, arg or None
}


def _iter_parameters(node: FunctionDef_) -> Iterator[tuple[ast.arg, _ParameterKind]]:
    for kind, attr in ARGS_KIND.items():
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
    _node: ast.Raise
    type: ast.expr | None  #   # noqa: A003

    def __repr__(self) -> str:
        exc = ast.unparse(self.type) if self.type else ""
        return f"{self.__class__.__name__}({exc})"


def iter_raises(node: FunctionDef_) -> Iterator[Raise]:
    """Yield raise nodes."""
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc:
            yield Raise(child, "", None, child.exc)


@dataclass(repr=False)
class Return(Object):  # noqa: D101
    _node: ast.expr | None
    type: ast.expr | None  #   # noqa: A003


def get_return(node: FunctionDef_) -> Return:
    """Yield raise nodes."""
    ret = node.returns
    return Return(ret, "", None, ret)


@dataclass(repr=False)
class Callable(Object):  # noqa: D101
    docstring: str | Docstring | None
    parameters: list[Parameter]
    decorators: list[ast.expr]
    type_params: list[ast.type_param]
    raises: list[Raise]


@dataclass(repr=False)
class Function(Callable):  # noqa: D101
    _node: FunctionDef_
    returns: Return

    def get_node(self) -> FunctionDef_:  # noqa: D102
        return self._node


@dataclass(repr=False)
class Class(Callable):  # noqa: D101
    _node: ClassDef
    bases: list[Class]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]

    def get(self, name: str) -> Attribute | Class | Function | None:  # noqa: D102
        for attr in ["attributes", "classes", "functions"]:
            for obj in getattr(self, attr):
                if obj.name == name:
                    return obj
        return None


def iter_callable_nodes(node: ast.Module | ClassDef) -> Iterator[Def]:
    """Yield callable nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield child


def _get_callable_args(
    node: Def,
) -> tuple[str, str | None, list[Parameter], list[ast.expr], list[ast.type_param]]:
    name = node.name
    docstring = ast.get_docstring(node)
    parameters = [] if isinstance(node, ClassDef) else list(iter_parameters(node))
    decorators = node.decorator_list
    type_params = node.type_params
    return name, docstring, parameters, decorators, type_params


def iter_callables(node: ast.Module | ClassDef) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for def_node in iter_callable_nodes(node):
        args = _get_callable_args(def_node)
        if isinstance(def_node, ClassDef):
            attrs = list(iter_attributes(def_node))
            classes, functions = get_callables(def_node)
            bases: list[Class] = []
            cls = Class(def_node, *args, [], bases, attrs, classes, functions)
            _move_property(cls)
            yield cls
        else:
            raises = list(iter_raises(def_node))
            yield Function(def_node, *args, raises, get_return(def_node))


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


@dataclass(repr=False)
class Module(Object):  # noqa: D101
    docstring: str | Docstring | None
    imports: list[Import]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]
    source: str

    def get(self, name: str) -> Import | Attribute | Class | Function | None:  # noqa: D102
        for attr in ["imports", "attributes", "classes", "functions"]:
            for obj in getattr(self, attr):
                if obj.name == name:
                    return obj
        return None

    def get_fullname(self) -> str:  # noqa: D102
        return self.name

    def get_source(self) -> str:
        """Return the source code."""
        return _get_source(self.name) if self.name else ""


cache_module_node: dict[str, tuple[float, ast.Module | None, str]] = {}
cache_module: dict[str, Module | None] = {}


def get_module(name: str) -> Module | None:
    """Return a [Module] instance by name."""
    if name in cache_module:
        return cache_module[name]
    if node := _get_module_node(name):
        current_module_name[0] = name
        module = _get_module_from_node(node)
        current_module_name[0] = None
        module.name = name
        module.source = _get_source(name)
        cache_module[name] = module
        return module
    cache_module[name] = None
    return None


def _get_module_from_node(node: ast.Module) -> Module:
    """Return a [Module] instance from [ast.Module] node."""
    docstring = ast.get_docstring(node)
    imports = list(iter_imports(node))
    attrs = list(iter_attributes(node))
    classes, functions = get_callables(node)
    return Module(node, "", docstring, imports, attrs, classes, functions, "")


def _get_module_node(name: str) -> ast.Module | None:
    """Return a [ast.Module] node by name."""
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
    if name in cache_module_node and mtime == cache_module_node[name][0]:
        return cache_module_node[name][1]
    with path.open(encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    cache_module_node[name] = (mtime, node, source)
    if name in cache_module:
        del cache_module[name]
    return node


def _get_source(name: str) -> str:
    if name in cache_module_node:
        return cache_module_node[name][2]
    return ""


def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    """Return a [Object] instance by name."""
    if module := get_module(fullname):
        return module
    if "." not in fullname:
        return None
    module_name, name = fullname.rsplit(".", maxsplit=1)
    if not (module := get_module(module_name)):
        return None
    return get_object_from_module(name, module)


def get_object_from_module(
    name: str,
    module: Module,
) -> Module | Class | Function | Attribute | None:
    """Return a [Object] instance by name from [Module]."""
    obj = module.get(name)
    if isinstance(obj, Import):
        return get_object(obj.fullname)
    return obj


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


def _merge_docstring_attribute(obj: Attribute) -> None:
    if doc := obj.docstring:
        type_, desc = split_attribute(doc)
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
        node = func.get_node()
        doc = func.docstring if isinstance(func.docstring, str) else ""
        type_ = func.returns.type
        type_params = func.type_params
        attr = Attribute(node, func.name, doc, type_, None, type_params)
        _merge_docstring_attribute(attr)
        obj.attributes.append(attr)
    obj.functions = funcs


def _get_style(doc: str) -> Style:
    for names in SECTION_NAMES:
        for name in names:
            if f"\n\n{name}\n----" in doc:
                current_docstring_style[0] = "numpy"
                return "numpy"
    current_docstring_style[0] = "google"
    return "google"


def _merge_docstring_attributes(obj: Module | Class, section: Section) -> None:
    print("----------------Attributes----------------")
    names = set([x.name for x in section.items] + [x.name for x in obj.attributes])
    print(names)
    attrs: list[Attribute] = []
    for name in names:
        if not (attr := get_by_name(obj.attributes, name)):
            attr = Attribute(None, name, None, None, None, [])  # type: ignore
        attrs.append(attr)
        if not (item := get_by_name(section.items, name)):
            continue
        item  # TODO
    obj.attributes = attrs


def _merge_docstring_parameters(obj: Class | Function, section: Section) -> None:
    print("----------------Parameters----------------")
    names = set([x.name for x in section.items] + [x.name for x in obj.parameters])
    print(names)
    for item in section:
        print(item)
    for attr in obj.parameters:
        print(attr)


def _merge_docstring_raises(obj: Class | Function, section: Section) -> None:
    print("----------------Raises----------------")
    # Fix raises.name
    names = set([x.name for x in section.items] + [x.name for x in obj.raises])
    print(names)


def _merge_docstring_returns(obj: Function, section: Section) -> None:
    print("----------------Returns----------------")
    print(section.description)
    print(obj.returns)


def merge_docstring(obj: Module | Class | Function) -> None:
    """Merge [Object] and [Docstring]."""
    sections: list[Section] = []
    if not (doc := obj.docstring) or not isinstance(doc, str):
        return
    style = _get_style(doc)
    docstring = parse_docstring(doc, style)
    for section in docstring:
        if section.name == "Attributes" and isinstance(obj, Module | Class):
            _merge_docstring_attributes(obj, section)
        elif section.name == "Parameters" and isinstance(obj, Class | Function):
            _merge_docstring_parameters(obj, section)
        elif section.name == "Raises" and isinstance(obj, Class | Function):
            _merge_docstring_raises(obj, section)
        elif section.name in ["Returns", "Yields"] and isinstance(obj, Function):
            _merge_docstring_returns(obj, section)
        else:
            sections.append(section)
    docstring.sections = sections
    obj.docstring = docstring


# def _resolve_bases(obj: Class) -> None:
#     obj.bases = [obj.get_module_name()]


# def merge_docstring(obj: Object, style: Style) -> None:
#     if isinstance(obj, Attribute):
#         return _merge_docstring_attribute(obj)
#     if isinstance(obj,
