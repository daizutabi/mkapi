"""Handle objects in the Abstract Syntax Tree (AST).

Provide classes and functions for representing and manipulating
various types of objects within the Abstract Syntax Tree (AST) of Python code.
Include representations for modules, classes, functions, attributes, and
properties, allowing for detailed analysis and processing of Python code
structures.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

import mkapi.ast
import mkapi.node
import mkapi.utils
from mkapi.ast import (
    Parameter,
    TypeAlias,
    get_assign_name,
    get_assign_type,
    is_assign,
    is_classmethod,
    is_function,
    is_property,
    is_staticmethod,
    iter_parameters,
    iter_raises,
)
from mkapi.doc import create_doc, create_doc_comment, is_empty, merge, split_type
from mkapi.node import get_fullname_from_module
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    get_module_source,
    get_object_from_module,
    is_dataclass,
    is_enum,
    is_package,
    split_module_name,
)

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator

    from mkapi.doc import Doc


def _qualname(name: str, parent: Parent | None) -> str:
    return f"{parent.qualname}.{name}" if parent else name


def _fullname(name: str, module: str | None, parent: Parent | None) -> str:
    qualname = _qualname(name, parent)
    return f"{module}.{qualname}" if module else name


@dataclass
class Object:
    """Represents a generic object in the Abstract Syntax Tree (AST).

    Serve as a base representation for various types of objects
    in the AST, encapsulating common attributes and behaviors. Each object
    is characterized by its name, the corresponding AST node, the module
    it belongs to, its parent object, and its fully qualified name.

    Attributes:
        name (str): The name of the object, typically representing the
            identifier in the source code.
        node (AST): The actual AST node associated with this object,
            providing access to the underlying structure of the code.
        module (str): The name of the module in which the object is defined.
        parent (Parent | None): The parent object of this object, if any.
        qualname (str): The qualified name of the object, combining
            the parent's qualified name and its name.
        fullname (str): The fully qualified name of the object, which may
            include module or package information, allowing for unique
            identification within the codebase.
        doc (Doc): The `Doc` instance of documentation associated with
            the object, extracted from the AST node or the object's
            docstring.
    """

    name: str
    """The name of the object."""

    node: AST
    """The AST node associated with this object."""

    module: str
    """The name of the module in which the object is defined."""

    parent: Parent | None
    """The parent object of this object, if any."""

    qualname: str = field(init=False)
    """The qualified name of the object."""

    fullname: str = field(init=False)
    """The fully qualified name of the object."""

    doc: Doc = field(init=False)
    """The documentation associated with the object."""

    def __post_init__(self):
        """Initialize the qualified and full names of the object."""
        self.qualname = _qualname(self.name, self.parent)
        self.fullname = _fullname(self.name, self.module, self.parent)
        objects[self.fullname] = self

        node = self.node
        types = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        text = ast.get_docstring(node) if isinstance(node, types) else node.__doc__  # type: ignore
        self.doc = create_doc(text)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"

    @property
    def kind(self) -> str:
        """The kind of the object."""
        return get_object_kind(self)


objects: dict[str, Object] = cache({})


def iter_child_objects(
    node: AST,
    module: str,
    parent: Parent | None,
) -> Iterator[Object]:
    """Iterate over child objects of a given AST node.

    Traverse the child nodes of the specified Abstract Syntax Tree
    (AST) node and yield instances of `Object` for each recognized
    child node type. Identify classes, functions, properties, and
    attributes within the AST structure, allowing for easy access
    to the components of the code.

    Args:
        node (AST): The AST node from which to iterate child objects.
        module (str): The name of the module in which the node is defined.
        parent (Parent | None): The parent object of the current node,
            if applicable. This is used to maintain the hierarchy of
            objects.

    Yields:
        Object: The instances of `Object` representing each recognized child
        node, such as a class, function, property, or attribute.
    """
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            yield create_class(child, module, parent)

        elif is_function(child):
            yield create_function(child, module, parent)

        elif is_property(child):
            yield create_property(child, module, parent)

        elif is_assign(child) and (name := get_assign_name(child)):
            yield create_attribute(name, child, module, parent)


@dataclass(repr=False)
class Type(Object):
    """Represents a type in the Abstract Syntax Tree (AST).

    Specialized representation of a type, which can be
    associated with variables, function parameters, and
    other constructs in Python code. Inherit from the `Object` class
    and includes additional attributes specific to type information.

    Attributes:
        type (ast.expr | None): The AST expression representing the type,
            or None if the type is not specified. This can include type
            annotations, type hints, or other expressions that define the
            type of an object.
    """

    type: ast.expr | None
    """The AST expression representing the type, or None
    if the type is not specified."""

    def __post_init__(self):
        super().__post_init__()
        split_type(self.doc)


@dataclass(repr=False)
class Attribute(Type):
    """Represent an attribute in the Abstract Syntax Tree (AST).

    Specialized representation of an attribute. Inherit from the `Type` class
    and includes additional attributes specific to attribute information.

    Attributes:
        name (str): The name of the attribute.
        node (ast.AnnAssign | ast.Assign | TypeAlias): The AST node
            associated with this attribute.
        module (str): The name of the module in which the attribute is defined.
        parent (Parent | None): The parent object of this attribute, if any.
        type (ast.expr | None): The AST expression representing the type,
            or None if the type is not specified.
        default (ast.expr | None): The default value of the attribute, if any.
    """

    node: ast.AnnAssign | ast.Assign | TypeAlias
    """The AST node associated with this attribute."""

    default: ast.expr | None
    """The default value of the attribute, if any."""


@dataclass(repr=False)
class Property(Type):
    """Represent a property in the Abstract Syntax Tree (AST).

    Specialized representation of a property. Inherit from the `Type` class
    and includes additional attributes specific to property information.

    Attributes:
        name (str): The name of the property.
        node (ast.FunctionDef | ast.AsyncFunctionDef): The AST node
            associated with this property.
        module (str): The name of the module in which the property is defined.
        parent (Parent | None): The parent object of this property, if any.
        type (ast.expr | None): The AST expression representing the type,
            or None if the type is not specified.
    """

    node: ast.FunctionDef | ast.AsyncFunctionDef
    """The AST node associated with this property."""


def create_attribute(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,
    module: str,
    parent: Parent | None,
) -> Attribute:
    """Create an `Attribute` object from the given parameters.

    Construct an instance of the `Attribute` class, which
    represents an attribute in the Abstract Syntax Tree (AST). Extract
    relevant information from the provided AST node and associate it with
    the attribute.

    Args:
        name (str): The name of the attribute.
        node (ast.AnnAssign | ast.Assign | TypeAlias): The AST node
            associated with this attribute.
        module (str): The name of the module in which the attribute is defined.
        parent (Parent | None): The parent object of this attribute, if any.

    Returns:
        Attribute: An instance of the `Attribute` class representing the
        specified attribute, including its name, node, module, parent, and
        any associated type information.
    """
    type_ = get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Attribute(name, node, module, parent, type_, default)


def create_property(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: Parent | None,
) -> Property:
    """Create a Property object from the given parameters.

    Construct an instance of the `Property` class, which
    represents a property in the Abstract Syntax Tree (AST). Extract
    relevant information from the provided AST node and associate it with
    the property.

    Args:
        node (ast.FunctionDef | ast.AsyncFunctionDef): The AST node
            associated with this property.
        module (str): The name of the module in which the property is defined.
        parent (Parent | None): The parent object of this property, if any.

    Returns:
        Property: An instance of the `Property` class representing the
        specified property, including its name, node, module, parent, and
        any associated type information.
    """
    return Property(node.name, node, module, parent, node.returns)


T = TypeVar("T")


@dataclass(repr=False)
class Parent(Object):
    """Represent a parent node in the Abstract Syntax Tree (AST).

    Specialized subclass of the `Object` class that
    manages child objects, allowing for hierarchical relationships
    between objects in the AST structure. Provide methods to
    retrieve child objects by name or type, facilitating the
    organization and manipulation of AST nodes.

    Attributes:
        children (dict[str, Object]): A dictionary that stores child
            objects, where the keys are the names of the children and
            the values are instances of `Object`.
    """

    children: dict[str, Object] = field(default_factory=dict, init=False)
    """A dictionary that stores child objects, where the keys are the names
    of the children and the values are instances of `Object`."""

    def get(self, name: str, type_: type[T] = Object) -> T | None:
        """Retrieve a child object by name, ensuring it is of the specified type.

        Args:
            name (str): The name of the child object to retrieve.
            type_ (type[T]): The type of the child object to ensure.

        Returns:
            T | None: The child object if found and of the specified type,
            otherwise None.
        """
        child = self.children.get(name)

        return child if isinstance(child, type_) else None

    def get_children(self, type_: type[T] = Object) -> list[tuple[str, T]]:
        """Retrieve a list of the child objects of the specified type.

        Args:
            type_ (type[T]): The type of the child objects to retrieve.

        Returns:
            list[tuple[str, T]]: A list of tuples, where each tuple contains
            the name and the child object, ensuring the object is of the
            specified type.
        """
        it = self.children.items()
        return [(name, obj) for (name, obj) in it if isinstance(obj, type_)]


def iter_objects(obj: Object, type_: type[T] = Object) -> Iterator[T]:
    """Iterate over the child objects of the given object,
    ensuring they are of the specified type.

    Recursively traverse the children of the provided
    object and yields objects that match the specified type.
    Ensure that all objects in the hierarchy are of the desired type,
    allowing for consistent processing and analysis of the AST structure.

    Args:
        obj (Object): The object whose children are to be iterated over.
        type_ (type[T]): The type of the child objects to ensure.

    Yields:
        T: The objects that are children of the object and matches the specified type.
    """
    if not isinstance(obj, Parent):
        return

    for child in obj.children.values():
        if isinstance(child, type_):
            yield child

        if isinstance(child, Parent):
            yield from iter_objects(child, type_)


@dataclass(repr=False)
class Definition(Parent):
    """Represent a definition in the Abstract Syntax Tree (AST).

    Specialized representation of a definition, such as
    a class or function, within the AST. Inherit from the `Parent`
    class and includes additional attributes specific to definitions,
    such as parameters and exceptions that may be raised.

    Attributes:
        parameters (list[Parameter]): A list of parameters associated
            with the definition, representing the input values for
            functions or methods.
        raises (list[ast.expr]): A list of expressions representing
            the exceptions that may be raised by the definition.
    """

    parameters: list[Parameter]
    """A list of parameters associated with the definition,
    representing the input values for functions or methods."""

    raises: list[ast.expr]
    """A list of expressions representing the exceptions that may be
    raised by the definition."""

    def __post_init__(self):
        super().__post_init__()

        for obj in iter_child_objects(self.node, self.module, self):
            self.children[obj.name] = obj


@dataclass(repr=False)
class Class(Definition):
    """Represent a class definition in the Abstract Syntax Tree (AST).

    Specialized representation of a class within the AST.
    Inherit from the `Definition` class and includes additional attributes
    specific to class definitions.

    Attributes:
        node (ast.ClassDef): The actual AST node associated with this class
            definition, which contains the structure and properties of the
            class as defined in the source code.
    """

    node: ast.ClassDef
    """The actual AST node associated with this class definition."""

    # @property
    # def attributes(self) -> list[Type]:
    #     return [x for _, x in self.get_children(Type)]


@dataclass(repr=False)
class Function(Definition):
    """Represent a function definition in the Abstract Syntax Tree (AST).

    Specialized representation of a function within the AST.
    Inherit from the `Definition` class and includes additional attributes
    specific to function definitions.

    Attributes:
        node (ast.FunctionDef | ast.AsyncFunctionDef): The actual AST node
            associated with this function definition, which contains the structure
            and properties of the function as defined in the source code.
    """

    node: ast.FunctionDef | ast.AsyncFunctionDef
    """The actual AST node associated with this function definition."""


def create_class(node: ast.ClassDef, module: str, parent: Parent | None) -> Class:
    """Create a `Class` object from the given parameters.

    Construct an instance of the `Class` class, which represents
    a class definition in the Abstract Syntax Tree (AST). Extract relevant
    information from the provided AST node and associates it with the class.

    Args:
        node (ast.ClassDef): The AST node associated with this class definition.
        module (str): The name of the module in which the class is defined.
        parent (Parent | None): The parent object of this class, if any.

    Returns:
        Class: An instance of the `Class` class representing the specified class,
        including its name, node, module, parent, and any associated attributes.
    """
    fullname = _fullname(node.name, module, parent)
    if (cls := objects.get(fullname)) and isinstance(cls, Class):
        return cls

    cls = Class(node.name, node, module, parent, [], [])

    init = cls.children.get("__init__")

    if isinstance(init, Function):
        for attr in iter_attributes_from_function(init, cls):
            cls.children.setdefault(attr.name, attr)

        objs = sorted(cls.children.values(), key=lambda x: x.node.lineno)  # type: ignore
        cls.children = {obj.name: obj for obj in objs}

        cls.doc = merge(cls.doc, init.doc)

    children: dict[str, Object] = {}
    for base in get_base_classes(node.name, module):
        children |= base.children
    cls.children = children | cls.children

    if is_dataclass(node.name, module):
        params = iter_parameters_from_dataclass(cls)
        cls.parameters.extend(params)

    elif isinstance(init, Function):
        params = init.parameters[1:]
        cls.parameters.extend(params)

    return cls


def create_class_by_name(name: str, module: str, parent: Parent | None) -> Class | None:
    """Create a `Class` object from the given parameters.

    Construct an instance of the `Class` class representing
    a class definition in the Abstract Syntax Tree (AST). Extract relevant
    information from the provided AST node and associate it with the class.

    Args:
        name (str): The name of the class to create.
        module (str): The name of the module in which the class is defined.
        parent (Parent | None): The `Parent` object of this class, if any.

    Returns:
        Class | None: An instance of the `Class` class representing the specified
        class, including its name, node, module, parent, and any associated
        attributes, or None if the class cannot be created.
    """
    if node := get_module_node(module):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef) and child.name == name:
                return create_class(child, module, parent)

    return None


@cache
def get_base_classes(name: str, module: str) -> list[Class]:
    """Get the base classes of a class.

    Retrieve the base classes of a class by searching for
    the class definition in the module and its base classes. Use the
    `get_base_classes` utility function to get the base class names and
    modules, and then retrieve the corresponding `Class` objects from the
    cached `objects` dictionary.

    Args:
        name (str): The name of the class to get the base classes for.
        module (str): The name of the module in which the class is defined.

    Returns:
        list[Class]: A list of the `Class` instances representing the base classes
        of the specified class.
    """
    bases = []

    for basename, basemodule in mkapi.utils.get_base_classes(name, module):
        if cls := objects.get(f"{basemodule}.{basename}"):
            if isinstance(cls, Class):
                bases.append(cls)

        elif cls := create_class_by_name(basename, basemodule, None):
            bases.append(cls)

    return bases


def iter_attributes_from_function(
    func: Function, parent: Parent
) -> Iterator[Attribute]:
    """Iterate over attributes from a function.

    Iterate over the attributes of a function, creating
    `Attribute` objects for each attribute found. Use the `get_children`
    method to retrieve the attributes and ensure that the attributes are
    associated with the correct parent object.

    Args:
        func (Function): The function object containing the attributes.
        parent (Parent): The parent object to which the attributes belong.

    Yields:
        Attribute: `Attribute` instances of the function.
    """
    self = func.parameters[0].name

    for name, obj in func.get_children(Attribute):
        if name.startswith(f"{self}."):
            name_ = name[len(self) + 1 :]
            yield create_attribute(name_, obj.node, obj.module, parent)
            del func.children[name]


def iter_parameters_from_dataclass(cls: Class) -> Iterator[Parameter]:
    """Iterate over parameters from a dataclass.

    This function iterates over the parameters of a dataclass, creating
    Parameter objects for each parameter found. It uses the `get_children`
    method to retrieve the parameters and ensures that the parameters are
    associated with the correct parent object.

    Args:
        cls (Class): The dataclass object containing the parameters.

    Yields:
        Parameter: `Parameter` instances of the dataclass.
    """
    obj = get_object_from_module(cls.name, cls.module)

    if inspect.isclass(obj):
        for param in inspect.signature(obj).parameters.values():
            if (assign := cls.get(param.name)) and isinstance(assign, Attribute):
                args = (assign.name, assign.type, assign.default)
                yield Parameter(*args, param.kind)

            else:
                raise NotImplementedError


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: Parent | None,
) -> Function:
    """Create a `Function` instance from the given parameters.

    Construct an instance of the `Function` class, which represents
    a function definition in the Abstract Syntax Tree (AST). Extract relevant
    information from the provided AST node and associates it with the function.

    Args:
        node (ast.FunctionDef | ast.AsyncFunctionDef): The AST node
            associated with this function definition, which contains the structure
            and properties of the function as defined in the source code.
        module (str): The name of the module in which the function is defined.
        parent (Parent | None): The parent object of this function, if any.

    Returns:
        Function: An instance of the `Function` class representing the specified
        function, including its name, node, module, parent, and any associated
        attributes.
    """
    params = list(iter_parameters(node))
    raises = list(iter_raises(node))

    return Function(node.name, node, module, parent, params, raises)


@dataclass(repr=False)
class Module(Parent):
    """Represent a module in the Abstract Syntax Tree (AST).

    Specialized representation of a module within the AST,
    inheriting from the `Parent` class. Encapsulate the structure and
    properties of a Python module, including its child objects, which can
    be classes, functions, and other attributes defined within the module.

    Attributes:
        node (ast.Module): The actual AST node associated with this module.
        module (None): A placeholder for the module name, initialized to None.
        parent (None): A placeholder for the parent object, initialized to None.
    """

    node: ast.Module
    """The actual AST node associated with this module."""

    module: None = field(default=None, init=False)
    """A placeholder for the module name, initialized to None."""

    parent: None = field(default=None, init=False)
    """A placeholder for the parent object, initialized to None."""

    def __post_init__(self):
        super().__post_init__()

        for obj in iter_child_objects(self.node, self.name, None):
            self.children[obj.name] = obj


@cache
def create_module(
    name: str,
    node: ast.Module | None = None,
    source: str | None = None,
) -> Module | None:
    """Create a `Module` instance from the given parameters.

    Construct an instance of the `Module` class, which represents
    a module in the Abstract Syntax Tree (AST). Extract relevant information
    from the provided AST node and associates it with the module.

    Args:
        name (str): The name of the module to create.
        node (ast.Module | None): The AST node associated with this module.
            If None, the function attempts to retrieve the node from the module name.
        source (str | None): The source code of the module as a string. If provided,
            it is used to extract documentation comments for attributes within the
            module.

    Returns:
        Module | None: An instance of the `Module` class representing the specified
        module, including its name, node, and any associated attributes. Returns
        None if the module cannot be created.
    """
    if not node:
        if node_source := get_module_node_source(name):
            node, source = node_source
        else:
            return None

    module = Module(name, node)

    if source:
        lines = source.splitlines()
        for attr in iter_objects(module, Attribute):
            if not is_empty(attr.doc) or attr.module != name:
                continue

            if doc := _create_doc_comment(attr.node, lines):
                attr.doc = doc

    return module


def _create_doc_comment(node: AST, lines: list[str]) -> Doc | None:
    line = lines[node.lineno - 1][node.end_col_offset :].strip()  # type: ignore

    if line.startswith("#:"):
        return create_doc_comment(line[2:].strip())

    if node.lineno > 1:  # type: ignore
        line = lines[node.lineno - 2][node.col_offset :]  # type: ignore
        if line.startswith("#:"):
            return create_doc_comment(line[2:].strip())

    return None


def get_object_kind(obj: Object) -> str:
    """Return the kind of the given object.

    Determine the kind of the provided object and return a string representation
    of its kind. The function checks the specific type of the object and
    returns a corresponding label.

    Args:
        obj (Object): The object whose kind is to be determined.

    Returns:
        str: A string representing the kind of the object. Possible return
        values include:

        - package, module
        - class, dataclass, enum
        - function, method, classmethod, staticmethod
        - property
    """
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    if isinstance(obj, Class):
        if is_enum(obj.name, obj.module):
            return "enum"

        return "dataclass" if is_dataclass(obj.name, obj.module) else "class"

    if isinstance(obj, Function):
        if is_classmethod(obj.node):
            return "classmethod"

        if is_staticmethod(obj.node):
            return "staticmethod"

        return "method" if obj.parent else "function"

    return obj.__class__.__name__.lower()


def get_source(obj: Object) -> str | None:
    """Return the source code of an object.

    Retrieve the source code associated with the given object,
    which can be a `Module` or any other object that has a corresponding
    Abstract Syntax Tree (AST) node. Check the type of the object and
    use appropriate methods to obtain the source code.

    Args:
        obj (Object): The object whose source code is to be retrieved. This
            can be an instance of Module or any other object with an AST node.

    Returns:
        str | None: The source code of the object as a string if available,
        or None if the source code cannot be retrieved.
    """
    if isinstance(obj, Module):
        return get_module_source(obj.name)

    if source := get_module_source(obj.module):
        return ast.get_source_segment(source, obj.node)

    return None


def is_child(obj: Object, parent: Object | None) -> bool:
    """Return True if `obj` is a child of `parent`.

    Check if the given object (`obj`) is a child of the specified
    parent object. Compare the parent attribute of the object
    and the provided parent argument.

    Args:
        obj (Object): The object to check if it is a child.
        parent (Object | None): The parent object to compare against.
    """
    if parent is None or isinstance(obj, Module) or isinstance(parent, Module):
        return True

    return obj.parent is parent


@cache
def get_object(name: str, module: str | None = None) -> Object | None:
    """Retrieve an object by its name and optional module.

    Attempt to find and return an object based on the provided
    name and module. First construct the full name of the object
    and check if it exists in the cached objects. If the object
    is not found, attempt to split the full name into its component
    parts and create the module if necessary. The function will
    attempt to create a `Module` instance based on the object's name.

    Args:
        name (str): The name of the object to retrieve.
        module (str | None): The name of the module in which the object is defined.
            If None, a module name will be extracted from the name.

    Returns:
        Object | None: The `Object` instance corresponding to the specified name
        and module, or None if the object cannot be found or created.
    """
    if not (fullname := get_fullname_from_module(name, module)):
        return None

    if obj := objects.get(fullname):
        return obj

    if not (name_module := split_module_name(fullname)):
        return None

    name_, module = name_module
    if not name_:
        return None

    if not module:
        return create_module(name_)

    create_module(module)
    return objects.get(fullname)


def get_fullname_from_object(name: str, obj: Object) -> str | None:
    """Return the fully qualified name for `name` relative to the
    given `Object` instance.

    Construct the fully qualified name for `name` based
    on the context of the provided `Object` instance.
    Check the type of the object and resolve the fullname accordingly.

    Args:
        name (str): The name for which to retrieve the full name.
        obj (Object): The object instance that provides context for the name.

    Returns:
        str | None: The fully qualified name of the specified name relative
        to the object, or None if the fullname cannot be determined.
    """
    if isinstance(obj, Module):
        return get_fullname_from_module(name, obj.name)

    if isinstance(obj, Parent):
        if child := obj.get(name):
            return child.fullname

    if "." not in name:
        if obj.parent and obj.parent != obj:
            return get_fullname_from_object(name, obj.parent)

        return get_fullname_from_module(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if (obj_ := objects.get(parent)) and obj_ != obj:
        return get_fullname_from_object(name, obj_)

    if (obj.name == parent) and name_ != name:
        return get_fullname_from_object(name_, obj)

    if name_ := get_fullname_from_module(name):
        return name_

    return get_fullname_from_module(name, obj.module)
