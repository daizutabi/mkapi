"""Object module."""
from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import is_classmethod, is_function, is_property, is_staticmethod
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    is_package,
    iter_parent_module_names,
)

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from inspect import _ParameterKind


@dataclass
class Parameter:
    name: str
    type: ast.expr | None
    default: ast.expr | None
    kind: _ParameterKind


@dataclass
class Node:
    name: str
    node: ast.AST | None

    def __repr__(self) -> str:
        kind = get_kind(self)
        return f"{kind.title()}({self.name!r})"


@dataclass(repr=False)
class Import(Node):
    node: ast.Import | ast.ImportFrom
    module: str
    fullname: str


@dataclass(repr=False)
class Object(Node):
    qualname: str
    module: str
    doc: str | None


@dataclass(repr=False)
class Assign(Object):
    node: ast.AnnAssign | ast.Assign | TypeAlias  # type: ignore
    type: ast.expr | None
    default: ast.expr | None


@dataclass(repr=False)
class Property(Object):
    node: ast.FunctionDef | ast.AsyncFunctionDef
    type: ast.expr | None


@dataclass(repr=False)
class Callable(Object):
    parameters: list[Parameter]
    raises: list[ast.expr]
    dict: dict[str, Node]

    def get(self, name) -> Node | None:
        return self.dict.get(name)


@dataclass(repr=False)
class Class(Callable):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Callable):
    node: ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Module(Node):
    node: ast.Module | None
    doc: str | None
    dict: dict[str, Node]
    source: str

    def get(self, name) -> Node | None:
        return self.dict.get(name)


def _iter_nodes(node: ast.AST, module: str, parent: str | None = None) -> Iterator[Node]:
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            yield create_class(child, module, parent)

        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            if is_function(child):
                yield create_function(child, module, parent)
            elif is_property(child):
                yield create_property(child, module, parent)

        elif isinstance(child, ast.AnnAssign | ast.Assign | TypeAlias):
            if name := mkapi.ast.get_assign_name(child):
                yield create_assign(name, child, module, parent)

        elif isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(name, child, module, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_members_from_star(child, module, parent)
            else:
                for name, fullname in _iter_imports_from_import_from(child, module):
                    yield Import(name, child, module, fullname)


def _iter_imports_from_import(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_parent_module_names(alias.name):
                yield module_name, module_name


def _get_module_from_import_from(node: ast.ImportFrom, module: str) -> str:
    if not node.module:
        return module

    if not node.level:
        return node.module

    names = module.split(".")

    if is_package(module):  # noqa: SIM108
        prefix = ".".join(names[: len(names) - node.level + 1])

    else:
        prefix = ".".join(names[: -node.level])

    return f"{prefix}.{node.module}"


def _iter_imports_from_import_from(node: ast.ImportFrom, module: str) -> Iterator[tuple[str, str]]:
    module = _get_module_from_import_from(node, module)
    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_members_from_star(node: ast.ImportFrom, module: str, parent: str | None) -> Iterator[Node]:
    module = _get_module_from_import_from(node, module)
    if node_ := get_module_node(module):
        yield from _iter_nodes(node_, module, parent)


def create_class(node: ast.ClassDef, module: str, parent: str | None) -> Class:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    dict_ = _get_members(node, module, qualname)

    return Class(node.name, node, qualname, module, doc, [], [], dict_)


def create_function(node: ast.FunctionDef | ast.AsyncFunctionDef, module: str, parent: str | None) -> Function:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    params = [Parameter(*args) for args in mkapi.ast.iter_parameters(node)]
    raises = list(mkapi.ast.iter_raises(node))

    dict_ = _get_members(node, module, qualname)

    return Function(node.name, node, qualname, module, doc, params, raises, dict_)


def create_property(node: ast.FunctionDef | ast.AsyncFunctionDef, module: str, parent: str | None) -> Property:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    return Property(node.name, node, qualname, module, doc, node.returns)


def create_assign(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,  # type: ignore
    module: str,
    parent: str | None,
) -> Assign:
    qualname = f"{parent}.{name}" if parent else name
    doc = node.__doc__

    type_ = mkapi.ast.get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Assign(name, node, qualname, module, doc, type_, default)


def _create_module(name: str, node: ast.Module, source: str, *, resolve: bool) -> Module:
    doc = ast.get_docstring(node)
    dict_ = _get_members(node, name, None, resolve=resolve)

    module = Module(name, node, doc, dict_, source)

    it = (child for child in walk(module) if isinstance(child, Assign))
    _add_doc_comment(it, source)

    return module


@cache
def create_module(name: str, *, resolve: bool = True) -> Module | None:
    if not (node_source := get_module_node_source(name)):
        return None

    return _create_module(name, *node_source, resolve=resolve)


def _get_members(node: ast.AST, module: str, parent: str | None, *, resolve: bool = True) -> dict[str, Node]:
    members: dict[str, Node] = {}

    for member in _iter_nodes(node, module, parent):
        name = member.name

        if resolve and isinstance(node, ast.Module) and isinstance(member, Import):
            resolved = _resolve(member.fullname, parent)
            members[name] = resolved or member

        else:
            members[name] = member

    return members


@cache
def _resolve(fullname: str, parent: str | None = None) -> Node | None:
    """Resolve name."""
    if module := create_module(fullname, resolve=False):
        return module

    if "." not in fullname:
        return None

    module, name = fullname.rsplit(".", maxsplit=1)

    if not (node := get_module_node(module)):
        return None

    for member in _iter_nodes(node, module, parent):
        if member.name == name:
            if not isinstance(member, Import):
                return member

            if member.fullname == fullname:
                return None

            return _resolve(member.fullname)

    return None


@cache
def get_members(module: str) -> dict[str, Node]:
    if node := get_module_node(module):
        return _get_members(node, module, None)

    return {}


@cache
def get_members_all(module: str) -> dict[str, Module | Object | Assign]:
    members = importlib.import_module(module).__dict__
    if not (names := members.get("__all__")):
        return {}

    members = get_members(module)
    members_all = {}

    for name in names:
        if member := members.get(name):
            members_all[name] = member

    return members_all


def walk(obj: Module | Class | Function) -> Iterator[Node]:
    for child in obj.dict.values():
        yield child
        if isinstance(child, Module | Class | Function):
            yield from walk(child)


def _add_doc_comment(assigns: Iterable[Assign], source: str) -> None:
    lines = source.splitlines()

    for assign in assigns:
        if assign.doc:
            continue

        node = assign.node

        line = lines[node.lineno - 1][node.end_col_offset :].strip()

        if line.startswith("#:"):
            assign.doc = line[2:].strip()

        elif node.lineno > 1:
            line = lines[node.lineno - 2][node.col_offset :]
            if line.startswith("#:"):
                assign.doc = line[2:].strip()


# @cache
# def resolve(fullname: str) -> str | None:
#     if resolved := _resolve(fullname):
#         if not isinstance(resolved, Module):
#             return f"{resolved.module}.{resolved.name}"
#         else:
#             return resolved.name

#     if "." not in fullname:
#         return None

#     fullname, attr = fullname.rsplit(".", maxsplit=1)

#     if resolved := resolve(fullname):
#         return f"{resolved}.{attr}"

#     return None


# @cache
# def get_member(name: str, module: str) -> Module | Object | Assign | None:
#     """Return an object in the module."""
#     members = _get_members(module)

#     if member := members.get(name):
#         return member

#     if "." not in name:
#         return None

#     module, name = name.rsplit(".", maxsplit=1)

#     if (member := members.get(module)) and isinstance(member, Module):
#         return get_member(name, member.name)

#     return None


# @cache
# def get_fullname(name: str, module: str) -> str | None:
#     """Return the fullname of an object in the module."""
#     if name.startswith(module) or module.startswith(name):
#         return name

#     if member := get_member(name, module):
#         if isinstance(member, Module):
#             return _get_module_name(member.name)

#         module = _get_module_name(member.module)
#         return f"{module}.{member.name}"

#     return None


# def iter_decorator_names(obj: Class | Function) -> Iterator[str]:
#     """Yield decorator_names."""
#     for deco in obj.node.decorator_list:
#         deco_name = next(mkapi.ast.iter_identifiers(deco))

#         if name := get_fullname(deco_name, obj.module.name.str):
#             yield name

#         else:
#             yield deco_name


# def get_decorator(obj: Class | Function, name: str) -> ast.expr | None:
#     """Return a decorator expr by name."""
#     for deco in obj.node.decorator_list:
#         deco_name = next(mkapi.ast.iter_identifiers(deco))

#         if get_fullname(deco_name, obj.module.name.str) == name:
#             return deco

#         if deco_name == name:
#             return deco

#     return None


# def is_dataclass(cls: Class) -> bool:
#     """Return True if the [Class] instance is a dataclass."""
#     return get_decorator(cls, "dataclasses.dataclass") is not None


# def is_classmethod(func: Function) -> bool:
#     """Return True if the [Function] instance is a classmethod."""
#     return get_decorator(func, "classmethod") is not None


# def is_staticmethod(func: Function) -> bool:
#     """Return True if the [Function] instance is a staticmethod."""
#     return get_decorator(func, "staticmethod") is not None


# def _iter_names_all_ast(module: str) -> Iterator[str]:
#     if not (all_ := get_member("__all__", module)):
#         return

#     node = all_.node
#     if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.List | ast.Tuple):
#         return

#     for arg in node.value.elts:
#         if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
#             yield arg.value

# def create_attribute(
#     assign: Assign,
#     module: Module,
#     parent: Class | Function | None,
# ) -> Attribute:
#     """Return an [Attribute] instance."""
#     node = assign.node
#     module = module or _create_empty_module()

#     if assign.node:
#         if isinstance(assign.node, ast.FunctionDef | ast.AsyncFunctionDef):
#             text = ast.get_docstring(assign.node)
#         else:
#             text = assign.node.__doc__

#         doc = docstrings.parse(text)

#         if doc.text.str and (lines := doc.text.str.splitlines()):
#             if ":" in lines[0]:
#                 type_, lines[0] = (x.lstrip(" ").rstrip() for x in lines[0].split(":", maxsplit=1))
#                 doc.text.str = "\n".join(lines).strip()

#                 if not assign.type.expr:
#                     assign.type.expr = ast.Constant(type_)

#     else:
#         doc = Docstring(Name("Docstring"), Type(), assign.text, [])

#     name, type_, default = assign.name, assign.type, assign.default
#     return Attribute(name, node, doc, module, parent, type_, default)


# def iter_attributes(
#     node: ast.ClassDef | ast.Module | ast.FunctionDef | ast.AsyncFunctionDef,
#     module: Module,
#     parent: Class | Function | None,
#     self: str = "",
# ) -> Iterator[Attribute]:
#     for child in iter_assigns(node, self):
#         yield create_attribute(child, module, parent)


# def _merge_attributes(
#     attributes: list[Attribute],
#     module: Module,
#     parent_doc: Module | Class | Function | None,
#     parent_create: Class | Function | None,
# ) -> None:
#     """Merge attributes."""
#     sections = parent_doc.doc.sections if parent_doc else module.doc.sections

#     if section := get_by_type(sections, Assigns):
#         for attr in attributes:
#             _merge_attribute_docstring(attr, section)

#         for item in reversed(section.items):
#             attr = create_attribute(item, module, parent_create)
#             attributes.insert(0, attr)

#     if module.source:
#         _merge_attributes_comment(attributes, module.source)


# def _merge_attribute_docstring(attr: Attribute, section: Assigns):
#     if item := get_by_name(section.items, attr.name):
#         if not attr.doc.text.str:
#             attr.doc.text.str = item.text.str

#         if not attr.type.expr:
#             attr.type.expr = item.type.expr

#         index = section.items.index(item)
#         del section.items[index]


# @dataclass(repr=False)
# class Attributes(Section):
#     """Attributes section."""

#     items: list[Assign]  # Attribute -> Assign


# def _add_attributes_section(doc: Docstring, attrs: list[Attribute]):
#     """Add an Attributes section."""
#     items = []

#     for attr in attrs:
#         if attr.doc.sections:
#             item = create_summary_item(attr.name, attr.doc, attr.type)
#             items.append(item)
#         elif attr.doc.text.str:
#             item = Item(attr.name, attr.type, attr.doc.text)
#             items.append(item)

#     if not items:
#         return

#     section = Attributes(Name("Attributes"), Type(), Text(), items)

#     if section_assigns := get_by_type(doc.sections, Assigns):
#         index = doc.sections.index(section_assigns)
#         doc.sections[index] = section
#     else:
#         doc.sections.append(section)

#     return


# def _union_attributes(la: list[Attribute], lb: list[Attribute]) -> Iterator[Attribute]:
#     """Yield merged [Attribute] instances."""
#     for name in unique_names(la, lb):
#         a, b = get_by_name(la, name), get_by_name(lb, name)

#         if a and not b:
#             yield a

#         elif not a and b:
#             yield b

#         elif isinstance(a, Attribute) and isinstance(b, Attribute):
#             a.node = a.node if a.node else b.node
#             a.type = a.type if a.type.expr else b.type
#             a.doc = mkapi.docstrings.merge(a.doc, b.doc)
#             yield a


# def iter_base_classes(cls: Class) -> Iterator[Class]:
#     """Yield base classes."""
#     for node in cls.node.bases:
#         name = next(mkapi.ast.iter_identifiers(node))

#         if base := get_by_name(cls.module.classes, name):
#             yield base
#             continue

#         modulename = cls.module.name.str
#         if member := get_member(name, modulename):
#             if module := create_module(member.module):
#                 if base := get_by_name(module.classes, member.name):
#                     yield base


# base_classes: dict[str, list[Class]] = cache({})


# def create_base_classes(cls: Class) -> list[Class]:
#     if cls.fullname.str in base_classes:
#         return base_classes[cls.fullname.str]

#     bases = list(iter_base_classes(cls))

#     base_classes[cls.fullname.str] = bases
#     return bases


# def inherit_base_classes(cls: Class) -> None:
#     """Inherit objects from base classes."""
#     # TODO: fix InitVar, ClassVar for dataclasses.
#     bases = create_base_classes(cls)

#     for name in ["attributes", "functions", "classes"]:
#         members = {member.name.str: member for member in getattr(cls, name)}

#         for base in bases:
#             for member in getattr(base, name):
#                 members.setdefault(member.name.str, member)

#         setattr(cls, name, list(members.values()))


# def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
#     """Yield [Parameter] instances a for dataclass signature."""
#     if not cls.module or not (module_name := cls.module.name.str):
#         raise NotImplementedError

#     try:
#         module = importlib.import_module(module_name)
#     except ModuleNotFoundError:
#         return

#     members = dict(inspect.getmembers(module, inspect.isclass))
#     obj = members[cls.name.str]

#     for param in inspect.signature(obj).parameters.values():
#         if attr := get_by_name(cls.attributes, param.name):
#             args = (attr.name, attr.type, attr.doc.text, attr.default)
#             yield Parameter(*args, param.kind)

#         else:
#             raise NotImplementedError


# def _merge_init(cls: Class):
#     if not (init := get_by_name(cls.functions, "__init__")):
#         return

#     cls.parameters = init.parameters
#     cls.raises = init.raises

#     if init.parameters:
#         self = init.parameters[0].name.str

#         attrs = list(iter_attributes(init.node, cls.module, cls, self))
#         _merge_attributes(attrs, cls.module, init, cls)

#         attrs = _union_attributes(cls.attributes, attrs)

#         cls.attributes = sorted(attrs, key=lambda attr: attr.node.lineno if attr.node else -1)

#         update_attributes(cls.attributes)

#     cls.doc = mkapi.docstrings.merge(cls.doc, init.doc)
#     del_by_name(cls.functions, "__init__")


# @cache
# def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
#     if fullname in objects:
#         return objects[fullname]

#     for name in iter_parent_module_names(fullname):
#         if load_module(name) and fullname in objects:
#             return objects[fullname]

#     return None


# Member_: TypeAlias = Module | Class | Function | Attribute
# Parent: TypeAlias = Module | Class | Function | None
# Predicate: TypeAlias = Callable_[[Member_, Parent], bool] | None


# def is_member(
#     obj: Module | Class | Function | Attribute,
#     parent: Module | Class | Function | None,
# ) -> bool:
#     """Return True if obj is a member of parent."""
#     if parent is None or isinstance(obj, Module) or isinstance(parent, Module):
#         return True

#     if obj.parent is not parent:
#         return False

#     return obj.module is parent.module


# def iter_objects_with_depth(
#     obj: Module | Class | Function | Attribute,
#     maxdepth: int = -1,
#     predicate: Predicate = None,
#     depth: int = 0,
# ) -> Iterator[tuple[Module | Class | Function | Attribute, int]]:
#     """Yield [Object] instances and depth."""
#     if not predicate or predicate(obj, None):
#         yield obj, depth

#     if depth == maxdepth or isinstance(obj, Attribute):
#         return

#     for child in itertools.chain(obj.classes, obj.functions):
#         if not predicate or predicate(child, obj):
#             yield from iter_objects_with_depth(child, maxdepth, predicate, depth + 1)

#     if isinstance(obj, Module | Class):
#         for attr in obj.attributes:
#             if not predicate or predicate(attr, obj):
#                 yield attr, depth + 1


# def iter_objects(
#     obj: Module | Class | Function | Attribute,
#     maxdepth: int = -1,
#     predicate: Predicate = None,
# ) -> Iterator[Module | Class | Function | Attribute]:
#     """Yield [Object] instances."""
#     for child, _ in iter_objects_with_depth(obj, maxdepth, predicate, 0):
#         yield child


# # def _iter_classes(obj: Module | Class | Function | Alias) -> Iterator[Class | Alias]:
# #     yield from obj.classes
# #     if isinstance(obj, Module):
# #         for alias in obj.aliases:
# #             if isinstance(alias.obj, Class):
# #                 yield alias


# # def _iter_functions(obj: Module | Class | Function | Alias) -> Iterator[Function | Alias]:
# #     yield from obj.functions
# #     if isinstance(obj, Module):
# #         for alias in obj.aliases:
# #             if isinstance(alias.obj, Function):
# #                 yield alias


# # def _iter_attributes(obj: Module | Class | Alias) -> Iterator[Attribute | Alias]:
# #     yield from obj.attributes
# #     if isinstance(obj, Module):
# #         for alias in obj.aliases:
# #             if isinstance(alias.obj, Attribute):
# #                 yield alias


# def get_source(obj: Module | Class | Function | Attribute) -> str | None:
#     """Return the source code of an object."""
#     if isinstance(obj, Module):
#         return obj.source

#     if not obj.node:
#         return None

#     if (module := obj.module) and (source := module.source):
#         start, stop = obj.node.lineno - 1, obj.node.end_lineno
#         lines = source.split("\n")
#         return "\n".join(lines[start:stop]) + "\n"

#     return None


def is_method(func: Function) -> bool:
    return "." in func.qualname


def _get_kind_function(func: Function) -> str:
    if is_classmethod(func.node):
        return "classmethod"

    if is_staticmethod(func.node):
        return "staticmethod"

    return "method" if is_method(func) else "function"


def get_kind(obj: Node) -> str:
    """Return kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    # if isinstance(obj, Class):
    #     return "dataclass" if mkapi.inspect.is_dataclass(obj) else "class"

    if isinstance(obj, Function):
        return _get_kind_function(obj)

    # if isinstance(obj, Attribute):
    #     return "property" if isinstance(obj.node, ast.FunctionDef) else "attribute"

    return obj.__class__.__name__.lower()


# def is_empty(obj: Object) -> bool:
#     """Return True if a [Object] instance is empty."""
#     if isinstance(obj, Attribute) and not obj.doc.sections:
#         return True

#     if not docstrings.is_empty(obj.doc):
#         return False

#     if isinstance(obj, Function) and obj.name.str.startswith("_"):
#         return True

#     return False
