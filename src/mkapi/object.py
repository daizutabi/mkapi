"""Module for handling objects in the Abstract Syntax Tree (AST).

This module provides classes and functions for representing and manipulating
various types of objects within the Abstract Syntax Tree (AST) of Python code.
It includes representations for modules, classes, functions, attributes, and
properties, allowing for detailed analysis and processing of Python code
structures.

Key Features:
- Representation of AST nodes as Python objects, including their attributes
  and relationships.
- Functions to create, retrieve, and manipulate objects based on their
  definitions in the source code.
- Iteration utilities for traversing child objects and members within the
  AST structure.
- Support for type annotations and documentation extraction from AST nodes.

This module is intended for use in tools and libraries that analyze or
transform Python code, providing a structured way to work with the
components of the AST.
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
from mkapi.node import get_fullname
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    get_module_source,
    get_object_from_module,
    is_dataclass,
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

    This class serves as a base representation for various types of objects
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
        qualname (str): The qualified name of the object, combining its
            name and the parent's qualified name.
        fullname (str): The fully qualified name of the object, which may
            include module or package information, allowing for unique
            identification within the codebase.
        doc (Doc): The documentation associated with the object, extracted
            from the AST node or the object's docstring.

    This class is intended to be subclassed by more specific object types
    (e.g., Class, Function, Attribute) that require additional attributes
    or behaviors specific to their context within the AST.
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

    This function traverses the child nodes of the specified Abstract
    Syntax Tree (AST) node and yields instances of Object for each
    recognized child node type. It identifies classes, functions,
    properties, and attributes within the AST structure, allowing for
    easy access to the components of the code.

    Args:
        node (AST): The AST node from which to iterate child objects.
        module (str): The name of the module in which the node is defined.
        parent (Parent | None): The parent object of the current node,
            if applicable. This is used to maintain the hierarchy of
            objects.

    Yields:
        Object: An instance of Object representing each recognized child
        node, such as a class, function, property, or attribute.

    This function is useful for analyzing and processing the structure
    of Python code by providing a way to access and manipulate the
    components defined within a given AST node.
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

    This class is a specialized representation of a type, which can be
    associated with variables, function parameters, return values, and
    other constructs in Python code. It inherits from the `Object` class
    and includes additional attributes specific to type information.

    Attributes:
        type (ast.expr | None): The AST expression representing the type,
            or None if the type is not specified. This can include type
            annotations, type hints, or other expressions that define the
            type of an object.

    This class is intended to encapsulate type-related information within
    the AST, allowing for easier manipulation and analysis of type
    annotations and type hints in Python code.
    """

    type: ast.expr | None
    """The AST expression representing the type, or None
    if the type is not specified."""

    def __post_init__(self):
        super().__post_init__()
        split_type(self.doc)


@dataclass(repr=False)
class Attribute(Type):
    """Represents an attribute in the Abstract Syntax Tree (AST).

    This class is a specialized representation of an attribute, which can
    be associated with variables, function parameters, return values, and
    other constructs in Python code. It inherits from the `Type` class
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

    This class is intended to encapsulate attribute-related information
    within the AST, allowing for easier manipulation and analysis of
    attribute annotations and hints in Python code.
    """

    node: ast.AnnAssign | ast.Assign | TypeAlias
    """The AST node associated with this attribute."""

    default: ast.expr | None
    """The default value of the attribute, if any."""


@dataclass(repr=False)
class Property(Type):
    """Represents a property in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a property, which can
    be associated with variables, function parameters, return values, and
    other constructs in Python code. It inherits from the `Type` class
    and includes additional attributes specific to property information.

    Attributes:
        name (str): The name of the property.
        node (ast.FunctionDef | ast.AsyncFunctionDef): The AST node
            associated with this property.
        module (str): The name of the module in which the property is defined.
        parent (Parent | None): The parent object of this property, if any.
        type (ast.expr | None): The AST expression representing the type,
            or None if the type is not specified.

    This class is intended to encapsulate property-related information
    within the AST, allowing for easier manipulation and analysis of
    property annotations and hints in Python code.
    """

    node: ast.FunctionDef | ast.AsyncFunctionDef
    """The AST node associated with this property."""


def create_attribute(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,
    module: str,
    parent: Parent | None,
) -> Attribute:
    """Create an Attribute object from the given parameters.

    This function constructs an instance of the Attribute class, which
    represents an attribute in the Abstract Syntax Tree (AST). It extracts
    relevant information from the provided AST node and associates it with
    the attribute.

    Args:
        name (str): The name of the attribute, typically representing the
            identifier in the source code.
        node (ast.AnnAssign | ast.Assign | TypeAlias): The AST node
            associated with this attribute, which can be an assignment
            statement or a type alias.
        module (str): The name of the module in which the attribute is defined.
        parent (Parent | None): The parent object of this attribute, if any.
            This is used to maintain the hierarchy of objects.

    Returns:
        Attribute: An instance of the Attribute class representing the
        specified attribute, including its name, node, module, parent, and
        any associated type information.

    This function is useful for analyzing and processing attributes within
    the AST, allowing for easy access to their properties and relationships
    within the code structure.
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

    This function constructs an instance of the Property class, which
    represents a property in the Abstract Syntax Tree (AST). It extracts
    relevant information from the provided AST node and associates it with
    the property.

    Args:
        node (ast.FunctionDef | ast.AsyncFunctionDef): The AST node
            associated with this property, which can be a function definition
            for a property.
        module (str): The name of the module in which the property is defined.
        parent (Parent | None): The parent object of this property, if any.
            This is used to maintain the hierarchy of objects.

    Returns:
        Property: An instance of the Property class representing the
        specified property, including its name, node, module, parent, and
        any associated type information.

    This function is useful for analyzing and processing properties within
    the AST, allowing for easy access to their properties and relationships
    within the code structure.
    """
    return Property(node.name, node, module, parent, node.returns)


T = TypeVar("T")


@dataclass(repr=False)
class Parent(Object):
    """Represents a parent node in the Abstract Syntax Tree (AST).

    This class is a specialized subclass of the `Object` class that
    manages child objects, allowing for hierarchical relationships
    between objects in the AST structure. It provides methods to
    retrieve child objects by name or type, facilitating the
    organization and manipulation of AST nodes.

    Attributes:
        children (dict[str, Object]): A dictionary that stores child
            objects, where the keys are the names of the children and
            the values are instances of `Object`. This attribute is
            initialized with an empty dictionary and is not intended to
            be set during initialization.

    This class is intended to be subclassed by more specific object types
    that require additional attributes or behaviors specific to their
    context within the AST.
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
        """Retrieve a list of child objects of the specified type.

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
    """Iterate over child objects of a given object, ensuring they are of the specified type.

    This function recursively traverses the children of the provided
    object and yields objects that match the specified type. It ensures that
    all objects in the hierarchy are of the desired type, allowing for
    consistent processing and analysis of the AST structure.

    Args:
        obj (Object): The object whose children are to be iterated over.
        type_ (type[T]): The type of the child objects to ensure.

    Yields:
        T: An object that is a child of the object and matches the specified type.

    This function is useful for filtering and processing specific types of
    objects within the AST, providing a way to access and manipulate the
    components defined within a given object.
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
    """Represents a definition in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a definition, such as
    a class or function, within the AST. It inherits from the `Parent`
    class and includes additional attributes specific to definitions,
    such as parameters and exceptions that may be raised.

    Attributes:
        parameters (list[Parameter]): A list of parameters associated
            with the definition, representing the input values for
            functions or methods.
        raises (list[ast.expr]): A list of expressions representing
            the exceptions that may be raised by the definition.

    This class is intended to encapsulate the details of definitions
    within the AST, allowing for easier manipulation and analysis of
    function and class definitions in Python code.
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
    """Represents a class definition in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a class within the AST.
    It inherits from the `Definition` class and includes additional attributes
    specific to class definitions.

    Attributes:
        node (ast.ClassDef): The actual AST node associated with this class
            definition, which contains the structure and properties of the
            class as defined in the source code.

    This class is intended to encapsulate the details of class definitions
    within the AST, allowing for easier manipulation and analysis of class
    structures in Python code.
    """

    node: ast.ClassDef
    """The actual AST node associated with this class definition."""


@dataclass(repr=False)
class Function(Definition):
    """Represents a function definition in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a function within the AST.
    It inherits from the `Definition` class and includes additional attributes
    specific to function definitions.

    Attributes:
        node (ast.FunctionDef | ast.AsyncFunctionDef): The actual AST node
            associated with this function definition, which contains the structure
            and properties of the function as defined in the source code.

    This class is intended to encapsulate the details of function definitions
    within the AST, allowing for easier manipulation and analysis of function
    structures in Python code.
    """

    node: ast.FunctionDef | ast.AsyncFunctionDef
    """The actual AST node associated with this function definition."""


def create_class(node: ast.ClassDef, module: str, parent: Parent | None) -> Class:
    """Create a Class object from the given parameters.

    This function constructs an instance of the Class class, which represents
    a class definition in the Abstract Syntax Tree (AST). It extracts relevant
    information from the provided AST node and associates it with the class.

    Args:
        node (ast.ClassDef): The AST node associated with this class definition.
        module (str): The name of the module in which the class is defined.
        parent (Parent | None): The parent object of this class, if any.

    Returns:
        Class: An instance of the Class class representing the specified class,
        including its name, node, module, parent, and any associated attributes.

    This function is useful for analyzing and processing class definitions
    within the AST, allowing for easy access to their properties and
    relationships within the code structure.
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

    for base in get_base_classes(node.name, module):
        for name, obj in base.get_children():
            cls.children.setdefault(name, obj)

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
        name (str): Name of the class to create.
        module (str): Name of the module in which the class is defined.
        parent (Parent | None): Parent object of this class, if any.

    Returns:
        Class | None: Instance of the `Class` class representing the specified
        class, including its name, node, module, parent, and any associated
        attributes, or `None` if the class cannot be created.
    """
    if node := get_module_node(module):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef) and child.name == name:
                return create_class(child, module, parent)

    return None


@cache
def get_base_classes(name: str, module: str) -> list[Class]:
    """Get the base classes of a class.

    This function retrieves the base classes of a class by searching for
    the class definition in the module and its base classes. It uses the
    `get_base_classes` utility function to get the base class names and
    modules, and then retrieves the corresponding Class objects from the
    `objects` dictionary.

    Args:
        name (str): The name of the class to get the base classes for.
        module (str): The name of the module in which the class is defined.

    Returns:
        list[Class]: A list of Class objects representing the base classes
        of the specified class.

    This function is useful for analyzing and processing class inheritance
    structures within the AST, allowing for easy access to the base classes
    of a class and their associated information.
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

    This function iterates over the attributes of a function, creating
    Attribute objects for each attribute found. It uses the `get_children`
    method to retrieve the attributes and ensures that the attributes are
    associated with the correct parent object.

    Args:
        func (Function): The function object containing the attributes.
        parent (Parent): The parent object to which the attributes belong.

    Returns:
        Iterator[Attribute]: An iterator over the attributes of the function.

    This function is useful for analyzing and processing attributes within
    the AST, allowing for easy access to the attributes defined within a
    function and their associated information.
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

    Returns:
        Iterator[Parameter]: An iterator over the parameters of the dataclass.

    This function is useful for analyzing and processing parameters within
    the AST, allowing for easy access to the parameters defined within a
    dataclass and their associated information.
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
    """Create a Function object from the given parameters.

    This function constructs an instance of the Function class, which represents
    a function definition in the Abstract Syntax Tree (AST). It extracts relevant
    information from the provided AST node and associates it with the function.

    Args:
        node (ast.FunctionDef | ast.AsyncFunctionDef): The AST node
            associated with this function definition, which contains the structure
            and properties of the function as defined in the source code.
        module (str): The name of the module in which the function is defined.
        parent (Parent | None): The parent object of this function, if any.

    Returns:
        Function: An instance of the Function class representing the specified
        function, including its name, node, module, parent, and any associated
        attributes.

    This function is useful for analyzing and processing function definitions
    within the AST, allowing for easy access to their properties and
    relationships within the code structure.
    """
    params = list(iter_parameters(node))
    raises = list(iter_raises(node))

    return Function(node.name, node, module, parent, params, raises)


@dataclass(repr=False)
class Module(Parent):
    """Represents a module in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a module within the AST,
    inheriting from the `Parent` class. It encapsulates the structure and
    properties of a Python module, including its child objects, which can
    be classes, functions, and other attributes defined within the module.

    Attributes:
        node (ast.Module): The actual AST node associated with this module,
            which contains the structure and properties of the module as
            defined in the source code.
        module (None): A placeholder for the module name, initialized to None.
        parent (None): A placeholder for the parent object, initialized to None.

    This class is intended to facilitate the analysis and manipulation of
    modules within the AST, allowing for easy access to the components
    defined within a given module and their relationships to one another.
    It provides methods to retrieve child objects and manage the hierarchy
    of objects within the module.
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
    """Create a Module object from the given parameters.

    This function constructs an instance of the Module class, which represents
    a module in the Abstract Syntax Tree (AST). It extracts relevant information
    from the provided AST node and associates it with the module.

    Args:
        name (str): The name of the module to create.
        node (ast.Module | None): The AST node associated with this module,
            which contains the structure and properties of the module as defined
            in the source code. If None, the function attempts to retrieve the
            node from the module name.
        source (str | None): The source code of the module as a string. If provided,
            it is used to extract documentation comments for attributes within the
            module.

    Returns:
        Module | None: An instance of the Module class representing the specified
        module, including its name, node, and any associated attributes. Returns
        None if the module cannot be created.

    This function is useful for analyzing and processing modules within the AST,
    allowing for easy access to the components defined within a given module and
    their relationships to one another.
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

    This function determines the kind of the provided object, which can be
    a Module, Class, or Function, and returns a string representation of
    its kind. The function checks the specific type of the object and
    returns a corresponding label.

    Args:
        obj (Object): The object whose kind is to be determined.

    Returns:
        str: A string representing the kind of the object. Possible return
        values include "package", "module", "dataclass", "class", "function",
        "method", "classmethod", or "staticmethod", depending on the object's
        characteristics.

    This function is useful for categorizing and processing different types
    of objects within the Abstract Syntax Tree (AST) structure.
    """
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    if isinstance(obj, Class):
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

    This function retrieves the source code associated with the given object,
    which can be a Module or any other object that has a corresponding
    Abstract Syntax Tree (AST) node. It checks the type of the object and
    uses appropriate methods to obtain the source code.

    Args:
        obj (Object): The object whose source code is to be retrieved. This
            can be an instance of Module or any other object with an AST node.

    Returns:
        str | None: The source code of the object as a string if available,
        or None if the source code cannot be retrieved.

    This function is useful for analyzing and processing the source code
    of Python objects within the Abstract Syntax Tree (AST) structure.
    """
    if isinstance(obj, Module):
        return get_module_source(obj.name)

    if source := get_module_source(obj.module):
        return ast.get_source_segment(source, obj.node)

    return None


def is_child(obj: Object, parent: Object | None) -> bool:
    """Return True if obj is a child of parent.

    This function checks if the given object (obj) is a child of the specified
    parent object. It performs this check by comparing the parent attribute
    of the object and the provided parent argument.

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

    This function attempts to find and return an object based on the provided
    name and module. It first constructs the full name of the object and checks
    if it exists in the cached objects. If the object is not found, it attempts
    to split the full name into its component parts and create the module if
    necessary.

    Args:
        name (str): The name of the object to retrieve.
        module (str | None): The name of the module in which the object is defined.
            If None, the function will attempt to create the module based on the
            object's name.

    Returns:
        Object | None: The object corresponding to the specified name and module,
        or None if the object cannot be found or created.

    This function is useful for dynamically retrieving objects within the
    Abstract Syntax Tree (AST) structure, allowing for flexible access to
    components defined in Python code.
    """
    if not (fullname := get_fullname(name, module)):
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
    """Return the full name of `name` relative to the given Object instance.

    This function constructs the fully qualified name for a given name based
    on the context of the provided object. It checks the type of the object
    and determines how to resolve the full name accordingly.

    Args:
        name (str): The name for which to retrieve the full name.
        obj (Object): The object instance that provides context for the name.

    Returns:
        str | None: The fully qualified name of the specified name relative
        to the object, or None if the full name cannot be determined.

    This function is useful for resolving names within the context of
    modules and parent objects in the Abstract Syntax Tree (AST) structure,
    allowing for accurate identification of objects in the codebase.
    """
    if isinstance(obj, Module):
        return get_fullname(name, obj.name)

    if isinstance(obj, Parent):
        if child := obj.get(name):
            return child.fullname

    if "." not in name:
        if obj.parent:
            return get_fullname_from_object(name, obj.parent)

        return get_fullname(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if obj_ := objects.get(parent):
        return get_fullname_from_object(name, obj_)

    if obj.name == parent:
        return get_fullname_from_object(name_, obj)

    return get_fullname(name)
