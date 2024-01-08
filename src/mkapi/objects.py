"""AST module."""
from __future__ import annotations

import ast
import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi import docstrings
from mkapi.utils import del_by_name, get_by_name, unique_names

if TYPE_CHECKING:
    from collections.abc import Iterator
    from inspect import _ParameterKind

    from mkapi.docstrings import Docstring, Item, Section, Style


CURRENT_MODULE_NAME: list[str | None] = [None]


@dataclass
class Object:  # noqa: D101
    _node: ast.AST
    name: str
    docstring: str | None

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

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
        if not (module := self.get_module()) or not (source := module.source):
            return None
        start, stop = self._node.lineno - 1, self._node.end_lineno
        return "\n".join(source.split("\n")[start:stop][:maxline])

    def unparse(self) -> str:
        """Unparse the AST node and return a string expression."""
        return ast.unparse(self._node)


@dataclass
class Import(Object):  # noqa: D101
    _node: ast.Import | ast.ImportFrom = field(repr=False)
    docstring: str | None = field(repr=False)
    fullname: str
    from_: str | None
    object: Module | Class | Function | Attribute | None  # noqa: A003

    def get_fullname(self) -> str:  # noqa: D102
        return self.fullname


def iter_imports(node: ast.Module) -> Iterator[Import]:
    """Yield import nodes and names."""
    for child in mkapi.ast.iter_import_nodes(node):
        from_ = f"{child.module}" if isinstance(child, ast.ImportFrom) else None
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_}.{alias.name}" if from_ else name
            yield Import(child, name, None, fullname, from_, None)


@dataclass(repr=False)
class Attribute(Object):  # noqa: D101
    _node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    type_params: list[ast.type_param] | None


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
class Parameter(Object):  # noqa: D101
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
class Raise(Object):  # noqa: D101
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
class Return(Object):  # noqa: D101
    _node: ast.expr | None
    type: ast.expr | None  #   # noqa: A003


def get_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Return:
    """Return a [Return] instance."""
    return Return(node.returns, "", None, node.returns)


@dataclass(repr=False)
class Callable(Object):  # noqa: D101
    _node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    docstring: Docstring | None
    parameters: list[Parameter]
    decorators: list[ast.expr]
    type_params: list[ast.type_param]
    raises: list[Raise]
    parent: Class | Module | None

    def get_parameter(self, name: str) -> Parameter | None:  # noqa: D102
        return get_by_name(self.parameters, name)

    def get_fullname(self) -> str:  # noqa: D102
        if self.parent:
            return f"{self.parent.get_fullname()}.{self.name}"
        return f"...{self.name}"

    def get_node_docstring(self) -> str | None:
        """Return the docstring of the node."""
        return ast.get_docstring(self._node)


@dataclass(repr=False)
class Function(Callable):  # noqa: D101
    _node: ast.FunctionDef | ast.AsyncFunctionDef
    returns: Return

    def get(self, name: str) -> Parameter | None:  # noqa: D102
        return self.get_parameter(name)


@dataclass(repr=False)
class Class(Callable):  # noqa: D101
    _node: ast.ClassDef
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

    def get(self, name: str) -> Parameter | Attribute | Class | Function | None:  # noqa: D102
        if obj := self.get_parameter(name):
            return obj
        if obj := self.get_attribute(name):
            return obj
        if obj := self.get_class(name):
            return obj
        if obj := self.get_function(name):
            return obj
        return None


def _get_callable_args(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[
    list[Parameter],
    list[ast.expr],
    list[ast.type_param],
    list[Raise],
]:
    parameters = [] if isinstance(node, ast.ClassDef) else list(iter_parameters(node))
    decorators = node.decorator_list
    type_params = node.type_params
    raises = [] if isinstance(node, ast.ClassDef) else list(iter_raises(node))
    return parameters, decorators, type_params, raises


def iter_callables(node: ast.Module | ast.ClassDef) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for child in mkapi.ast.iter_callable_nodes(node):
        args = (child.name, None, *_get_callable_args(child), None)
        if isinstance(child, ast.ClassDef):
            bases: list[Class] = []
            attrs = list(iter_attributes(child))
            classes, functions = get_callables(child)
            yield Class(child, *args, bases, attrs, classes, functions)
        else:
            yield Function(child, *args, get_return(child))


def get_callables(
    node: ast.Module | ast.ClassDef,
) -> tuple[list[Class], list[Function]]:
    """Return a tuple of (list[Class], list[Function])."""
    classes: list[Class] = []
    functions: list[Function] = []
    for callable_node in iter_callables(node):
        if isinstance(callable_node, Class):
            classes.append(callable_node)
        else:
            functions.append(callable_node)
    return classes, functions


@dataclass(repr=False)
class Module(Object):  # noqa: D101
    _node: ast.Module
    docstring: Docstring | None
    imports: list[Import]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]
    source: str | None
    kind: str

    def get_fullname(self) -> str:  # noqa: D102
        return self.name

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source of the module."""
        if not self.source:
            return None
        return "\n".join(self.source.split("\n")[:maxline])

    def get_node_docstring(self) -> str | None:
        """Return the docstring of the node."""
        return ast.get_docstring(self._node)

    def get_import(self, name: str) -> Import | None:  # noqa: D102
        return get_by_name(self.imports, name)

    def get_attribute(self, name: str) -> Attribute | None:  # noqa: D102
        return get_by_name(self.attributes, name)

    def get_class(self, name: str) -> Class | None:  # noqa: D102
        return get_by_name(self.classes, name)

    def get_function(self, name: str) -> Function | None:  # noqa: D102
        return get_by_name(self.functions, name)

    def get(self, name: str) -> Import | Attribute | Class | Function | None:  # noqa: D102
        if obj := self.get_import(name):
            return obj
        if obj := self.get_attribute(name):
            return obj
        if obj := self.get_class(name):
            return obj
        if obj := self.get_function(name):
            return obj
        return None


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


CACHE_MODULE: dict[str, tuple[Module | None, float]] = {}


def get_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if name in CACHE_MODULE and not CACHE_MODULE[name][0]:
        return None
    if not (path := get_module_path(name)):
        CACHE_MODULE[name] = (None, 0)
        return None
    mtime = path.stat().st_mtime
    if name in CACHE_MODULE and mtime == CACHE_MODULE[name][1]:
        return CACHE_MODULE[name][0]
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    CURRENT_MODULE_NAME[0] = name  # Set the module name in a global cache.
    module = _get_module_from_node(node)
    CURRENT_MODULE_NAME[0] = None  # Remove the module name from a global cache.
    module.name = name
    module.source = source
    _postprocess(module)
    CACHE_MODULE[name] = (module, mtime)
    return module


def _get_module_from_node(node: ast.Module) -> Module:
    """Return a [Module] instance from the [ast.Module] node."""
    imports = list(iter_imports(node))
    attrs = list(iter_attributes(node))
    classes, functions = get_callables(node)
    return Module(node, "", None, imports, attrs, classes, functions, "", "")


def set_import_object(module: Module) -> None:
    """Set import object."""
    for import_ in module.imports:
        _set_import_object(import_)


def _set_import_object(import_: Import) -> None:
    if obj := get_module(import_.fullname):
        import_.object = obj
        return
    if "." not in import_.fullname:
        return
    module_name, name = import_.fullname.rsplit(".", maxsplit=1)
    module = get_module(module_name)
    if module and isinstance(obj := module.get(name), Class | Function | Attribute):
        import_.object = obj


CACHE_OBJECT: dict[str, Module | Class | Function] = {}


def _register_object(obj: Module | Class | Function) -> None:
    CACHE_OBJECT[obj.get_fullname()] = obj


def get_object(fullname: str) -> Module | Class | Function | None:
    """Return a [Object] instance by the fullname."""
    if module := get_module(fullname):
        return module
    if fullname in CACHE_OBJECT:
        return CACHE_OBJECT[fullname]
    if "." not in fullname:
        return None
    n = len(fullname.split("."))
    for maxsplit in range(1, n):
        module_name, *_ = fullname.rsplit(".", maxsplit)
        if module := get_module(module_name) and fullname in CACHE_OBJECT:
            return CACHE_OBJECT[fullname]
    return None


# ---------------------------------------------------------------------------------
# Docsting -> Object
# ---------------------------------------------------------------------------------

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
    return ast.Constant(value=name)


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
        node = func._node  # noqa: SLF001
        if isinstance(node, ast.AsyncFunctionDef) or not _is_property(func):
            funcs.append(func)
            continue
        doc = func.get_node_docstring()
        type_ = func.returns.type
        type_params = func.type_params
        attr = Attribute(node, func.name, doc, type_, None, type_params)
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
    # if not (doc := obj.docstring) or not isinstance(doc, str):
    #     return
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


def _set_parent(obj: Module | Class) -> None:
    for cls in obj.classes:
        cls.parent = obj
    for func in obj.functions:
        func.parent = obj


def _postprocess(obj: Module | Class) -> None:
    _set_parent(obj)
    _register_object(obj)
    _merge_docstring(obj)
    if isinstance(obj, Class):
        _move_property(obj)
    for attr in obj.attributes:
        _merge_attribute_docstring(attr)
    for cls in obj.classes:
        _postprocess(cls)
        _postprocess_class(cls)
    for func in obj.functions:
        _register_object(func)
        _merge_docstring(func)


ATTRIBUTE_ORDER_DICT = {
    ast.AnnAssign: 1,
    ast.Assign: 2,
    ast.FunctionDef: 3,
    ast.TypeAlias: 4,
}


def _attribute_order(attr: Attribute) -> int:
    node = attr._node  # noqa: SLF001
    if node is None:
        return 0
    return ATTRIBUTE_ORDER_DICT.get(type(node), 10)


def _postprocess_class(cls: Class) -> None:
    if init := cls.get_function("__init__"):
        cls.parameters = init.parameters
        cls.raises = init.raises
        cls.docstring = docstrings.merge(cls.docstring, init.docstring)  # type: ignore
        cls.attributes.sort(key=_attribute_order)
        del_by_name(cls.functions, "__init__")
    # TODO: dataclass, bases
