"""Object module."""
from __future__ import annotations

import ast
import importlib
import importlib.util
from dataclasses import InitVar, dataclass, field
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

    from mkapi.docstrings import Item, Section


@dataclass
class Type:
    """Type class."""

    expr: ast.expr
    markdown: str = field(default="", init=False)


@dataclass
class Text:
    """Text class."""

    str: str  # noqa: A003
    markdown: str = field(default="", init=False)


@dataclass
class Object:
    """Object base class."""

    node: ast.AST
    name: str
    module: Module | None = field(init=False)
    text: Text | None = field(init=False)
    type: Type | None = field(init=False)  # noqa: A003
    _text: InitVar[str | None]
    _type: InitVar[ast.expr | None]

    def __post_init__(self, _text: str | None, _type: ast.expr | None) -> None:
        self.module = Module.current
        self.text = Text(_text) if _text else None
        self.type = Type(_type) if _type else None
        if self.module and self.text:
            self.module.add_text(self.text)
        if self.module and self.type:
            self.module.add_type(self.type)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def get_source(self, maxline: int | None = None) -> str | None:
        """Return the source code segment."""
        if (module := self.module) and (source := module.source):
            start, stop = self.node.lineno - 1, self.node.end_lineno
            return "\n".join(source.split("\n")[start:stop][:maxline])
        return None

    def iter_types(self) -> Iterator[Type]:
        """Yield [Type] instances."""
        if self.type:
            yield self.type

    def iter_texts(self) -> Iterator[Text]:
        """Yield [Text] instances."""
        if self.text:
            yield self.text


@dataclass(repr=False)
class Parameter(Object):
    """Parameter class for [Class] and [Function]."""

    node: ast.arg | None
    default: ast.expr | None
    kind: _ParameterKind | None


def create_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    for arg, kind, default in mkapi.ast.iter_parameters(node):
        yield Parameter(arg, arg.arg, None, arg.annotation, default, kind)


@dataclass(repr=False)
class Raise(Object):
    """Raise class for [Class] and [Function]."""

    node: ast.Raise | None

    def __repr__(self) -> str:
        exc = ast.unparse(self.type.expr) if self.type else ""
        return f"{self.__class__.__name__}({exc})"


def create_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Raise]:
    """Yield [Raise] instances."""
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc:
            yield Raise(child, "", None, child.exc)


@dataclass(repr=False)
class Return(Object):
    """Return class for [Class] and [Function]."""

    node: ast.expr | None


def create_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Return:
    """Return a [Return] instance."""
    return Return(node.returns, "", None, node.returns)


@dataclass(repr=False)
class Import:
    """Import class for [Module]."""

    node: ast.Import | ast.ImportFrom
    name: str
    fullname: str
    from_: str | None
    level: int

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


def iter_imports(node: ast.Import | ast.ImportFrom) -> Iterator[Import]:
    """Yield [Import] instances."""
    for alias in node.names:
        name = alias.asname or alias.name
        if isinstance(node, ast.Import):
            for parent in iter_parent_modulenames(name):
                # TODO: ex. import matplotlib.pyplot as plt
                yield Import(node, parent, parent, None, 0)
        else:
            from_ = f"{node.module}"
            fullname = f"{from_}.{alias.name}"
            yield Import(node, name, fullname, from_, node.level)


objects: dict[str, Attribute | Class | Function | Module | None] = {}


@dataclass(repr=False)
class Member(Object):
    """Member class for [Attribute], [Function], [Class], and [Module]."""

    qualname: str = field(init=False)
    fullname: str = field(init=False)

    def __post_init__(self, _text: str | None, _type: ast.expr | None) -> None:
        super().__post_init__(_text, _type)
        qualname = Class.classnames[-1]
        self.qualname = f"{qualname}.{self.name}" if qualname else self.name
        m_name = self.module.name if self.module else "__mkapi__"
        self.fullname = f"{m_name}.{self.qualname}" if m_name else self.qualname
        objects[self.fullname] = self  # type:ignore

    def iter_members(self) -> Iterator[Member]:
        """Yield [Member] instances."""
        yield from []


@dataclass(repr=False)
class Attribute(Member):
    """Atrribute class for [Module] and [Class]."""

    node: ast.AnnAssign | ast.Assign | ast.TypeAlias | ast.FunctionDef | None
    default: ast.expr | None


def create_attribute(node: ast.AnnAssign | ast.Assign | ast.TypeAlias) -> Attribute:
    """Return an [Attribute] instance."""
    name = mkapi.ast.get_assign_name(node) or ""
    type_ = mkapi.ast.get_assign_type(node)
    text, type_ = _attribute_text_type(node.__doc__, type_)
    default = None if isinstance(node, ast.TypeAlias) else node.value
    return Attribute(node, name, text, type_, default)


def create_attribute_from_property(node: ast.FunctionDef) -> Attribute:
    """Return an [Attribute] instance from a property."""
    doc = ast.get_docstring(node)
    type_ = node.returns
    text, type_ = _attribute_text_type(doc, type_)
    return Attribute(node, node.name, text, type_, None)


def _attribute_text_type(
    doc: str | None,
    type_: ast.expr | None,
) -> tuple[str | None, ast.expr | None]:
    if not doc:
        return doc, type_
    type_doc, text = docstrings.split_without_name(doc, "google")
    if not type_ and type_doc:
        # ex. list(str) -> list[str]
        type_doc = type_doc.replace("(", "[").replace(")", "]")
        type_ = mkapi.ast.create_expr(type_doc)
    return text, type_


@dataclass(repr=False)
class Callable(Member):
    """Callable class for [Class] and [Function]."""

    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    parameters: list[Parameter]
    raises: list[Raise]

    def get_parameter(self, name: str) -> Parameter | None:
        """Return a [Parameter] instance by the name."""
        return get_by_name(self.parameters, name)

    def get_raise(self, name: str) -> Raise | None:
        """Return a [Riase] instance by the name."""
        return get_by_name(self.raises, name)


def _callable_args(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str | None, None, list[Parameter], list[Raise]]:
    text = ast.get_docstring(node)
    if isinstance(node, ast.ClassDef):
        return text, None, [], []
    parameters = list(create_parameters(node))
    raises = list(create_raises(node))
    return text, None, parameters, raises


@dataclass(repr=False)
class Function(Callable):
    """Function class."""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    returns: Return


def get_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Function:
    """Return a [Function] instance."""
    return Function(node, node.name, *_callable_args(node), create_return(node))


@dataclass(repr=False)
class Class(Callable):
    """Class class."""

    node: ast.ClassDef
    attributes: list[Attribute] = field(default_factory=list, init=False)
    classes: list[Class] = field(default_factory=list, init=False)
    functions: list[Function] = field(default_factory=list, init=False)
    bases: list[Class] = field(default_factory=list, init=False)
    classnames: ClassVar[list[str | None]] = [None]

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


def create_class(node: ast.ClassDef) -> Class:
    """Return a [Class] instance."""
    name = node.name
    cls = Class(node, node.name, *_callable_args(node))
    qualname = f"{Class.classnames[-1]}.{name}" if Class.classnames[-1] else name
    Class.classnames.append(qualname)
    for member in create_members(node):
        cls.add_member(member)
    Class.classnames.pop()
    return cls


def create_members(
    node: ast.ClassDef | ast.Module,
) -> Iterator[Import | Attribute | Class | Function]:
    """Yield members."""
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef):  # noqa: SIM102
            if mkapi.ast.is_property(child.decorator_list):
                yield create_attribute_from_property(child)
                continue
        if isinstance(child, ast.Import | ast.ImportFrom):
            yield from iter_imports(child)
        elif isinstance(child, ast.AnnAssign | ast.Assign | ast.TypeAlias):
            attr = create_attribute(child)
            if attr.name:
                yield attr
        elif isinstance(child, ast.ClassDef):
            yield create_class(child)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            yield get_function(child)


@dataclass(repr=False)
class Module(Member):
    """Module class."""

    node: ast.Module
    imports: list[Import] = field(default_factory=list, init=False)
    attributes: list[Attribute] = field(default_factory=list, init=False)
    classes: list[Class] = field(default_factory=list, init=False)
    functions: list[Function] = field(default_factory=list, init=False)
    types: list[Type] = field(default_factory=list, init=False)
    texts: list[Text] = field(default_factory=list, init=False)
    source: str | None = None
    kind: str | None = None
    current: ClassVar[Self | None] = None

    def __post_init__(self, _text: str | None, _type: ast.expr | None) -> None:
        super().__post_init__(_text, _type)
        self.qualname = self.fullname = self.name
        modules[self.name] = self

    def add_type(self, type_: Type) -> None:
        """Add a [Type] instance."""
        self.types.append(type_)

    def add_text(self, text: Text) -> None:
        """Add a [Text] instance."""
        self.texts.append(text)

    def add_member(self, member: Import | Attribute | Class | Function) -> None:
        """Add a member instance."""
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

    def get_member(self, name: str) -> Import | Attribute | Class | Function | None:
        """Return a member instance by the name."""
        if obj := self.get_import(name):
            return obj
        if obj := self.get_attribute(name):
            return obj
        if obj := self.get_class(name):
            return obj
        if obj := self.get_function(name):
            return obj
        return None

    def get_fullname(self, name: str | None = None) -> str | None:
        """Return the fullname of the module."""
        if not name:
            return self.name
        if obj := self.get_member(name):
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

    def _get_link(self, name: str) -> str:
        fullname = self.get_fullname(name)
        if fullname:
            return f"[{name}][__mkapi__.{fullname}]"
        return name

    def set_markdown(self) -> None:
        """Set markdown with link form."""
        for type_ in self.types:
            type_.markdown = mkapi.ast.unparse(type_.expr, self._get_link)


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
    module = create_module_from_node(node, name)
    module.source = source
    return module


def create_module_from_node(node: ast.Module, name: str = "__mkapi__") -> Module:
    """Return a [Module] instance from the [ast.Module] node."""
    text = ast.get_docstring(node)
    module = Module(node, name, text, None)
    if Module.current is not None:
        raise NotImplementedError
    Module.current = module
    for member in create_members(node):
        module.add_member(member)
    Module.current = None
    _postprocess(module)
    return module
    # with Module.create(node, name) as module:
    #     for member in create_members(node):
    #         module.add_member(member)
    # return module


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
        obj.type = Type(mkapi.ast.create_expr(type_))
    obj.text = Text(item.text)  # Does item.text win?


def _new(
    cls: type[Attribute | Parameter | Raise],
    name: str,
) -> Attribute | Parameter | Raise:
    args = (None, name, None, None)
    if cls is Attribute:
        return Attribute(*args, None)
    if cls is Parameter:
        return Parameter(*args, None, None)
    if cls is Raise:
        return Raise(*args)
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
    if not obj.text:
        return
    sections: list[Section] = []
    for section in docstrings.parse(obj.text.str):
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
    if not attr.node:
        return 0
    return ATTRIBUTE_ORDER_DICT.get(type(attr.node), 10)


def _iter_base_classes(cls: Class) -> Iterator[Class]:
    """Yield base classes.

    This function is called in postprocess for setting base classes.
    """
    if not cls.module:
        return
    for node in cls.node.bases:
        base_name = next(mkapi.ast.iter_identifiers(node))
        base_fullname = cls.module.get_fullname(base_name)
        if not base_fullname:
            continue
        base = get_object(base_fullname)
        if base and isinstance(base, Class):
            yield base


def _inherit(cls: Class, name: str) -> None:
    # TODO: fix InitVar, ClassVar for dataclasses.
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
        # cls.docstring = docstrings.merge(cls.docstring, init.docstring)
        cls.attributes.sort(key=_attribute_order)
        del_by_name(cls.functions, "__init__")
    if mkapi.dataclasses.is_dataclass(cls):
        for attr, kind in mkapi.dataclasses.iter_parameters(cls):
            args = (None, attr.name, None, None, attr.default, kind)
            parameter = Parameter(*args)
            parameter.text = attr.text
            parameter.type = attr.type
            parameter.module = attr.module
            cls.parameters.append(parameter)
