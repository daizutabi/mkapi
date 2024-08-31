"""
Node Representation Module for Abstract Syntax Tree (AST)

This module provides classes and functions for representing and manipulating
nodes in the Abstract Syntax Tree (AST) of Python code. The AST is a
tree representation of the abstract syntactic structure of source code,
which allows for programmatic analysis and transformation of Python code.

Usage:
This module is intended for use in code analysis, refactoring, and
metaprogramming tasks. It can be used to programmatically inspect and
modify Python code by manipulating its AST. Developers can leverage the
provided classes and functions to build tools for static analysis,
code generation, and other advanced programming tasks.

This module is designed to facilitate the analysis and transformation of
Python code at the syntactic level, enabling developers to create tools
for code generation, refactoring, and static analysis. It is intended for
internal use within the application and may be subject to changes as the
application evolves. Developers are encouraged to refer to the class and
function docstrings for detailed information on each component's purpose,
parameters, and return values.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import TypeAlias, get_assign_name, is_assign
from mkapi.utils import (
    cache,
    get_module_node,
    get_object_from_module,
    is_package,
    iter_attribute_names,
    list_exported_names,
    split_module_name,
)

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator


@dataclass
class Node:
    """Represents a generic node in the Abstract Syntax Tree (AST).

    This class serves as a base representation for various types of nodes
    in the AST, encapsulating common attributes and behaviors. Each node
    is characterized by its name, the corresponding AST node, and its
    fully qualified name.

    This class is intended to be subclassed by more specific node types
    (e.g., Import, Object, Definition) that require additional attributes
    or behaviors specific to their context within the AST.
    """

    name: str
    """The name of the node."""

    node: AST
    """The AST node associated with this representation."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass(repr=False)
class Import(Node):
    """Represents an import statement in the Abstract Syntax Tree (AST).

    This class is a specialized representation of an import statement,
    which can either be a standard import or an import from a specific
    module. It inherits from the `Node` class and includes additional
    attributes specific to import statements.

    This class is intended to encapsulate the details of import statements
    within the AST, allowing for easier manipulation and analysis of
    import-related information in Python code.
    """

    node: ast.Import | ast.ImportFrom
    """The actual AST node associated with this import statement,
    which can be either an `Import` or `ImportFrom` node from the `ast` module.
    """

    fullname: str
    """The fully qualified name of the import statement,
    including the module and any aliases."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r} -> {self.fullname!r})"


@dataclass(repr=False)
class Object(Node):
    """Represents an object (e.g., class, function, method) in the Abstract Syntax Tree (AST).

    This class is a specialized representation of an object, such as a class,
    function, or method, within the AST. It inherits from the `Node` class
    and includes additional attributes specific to object representations.

    This class is intended to be subclassed by more specific object types
    (e.g., `Class`, `Function`, `Method`) that require additional attributes
    or behaviors specific to their context within the AST.
    """

    module: str
    """The module in which the object is defined."""


@dataclass(repr=False)
class Definition(Object):
    """Represents a definition (e.g., class, function, method) in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a definition, such as a class,
    function, or method, within the AST. It inherits from the `Object` class
    and includes additional attributes specific to definition representations.

    This class is intended to be subclassed by more specific definition types
    (e.g., `Class`, `Function`, `Method`) that require additional attributes
    or behaviors specific to their context within the AST.
    """

    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    """The actual AST node associated with this definition, which can be a class definition,
    a function definition, or an asynchronous function definition from the `ast` module."""


@dataclass(repr=False)
class Assign(Object):
    """Represents an assignment statement in the Abstract Syntax Tree (AST).

    This class is a specialized representation of an assignment statement,
    which can be either an annotated assignment or a simple assignment.
    It inherits from the `Object` class and includes additional attributes
    specific to assignment representations.

    This class is intended to encapsulate the details of assignment statements
    within the AST, allowing for easier manipulation and analysis of
    assignment-related information in Python code.
    """

    node: ast.AnnAssign | ast.Assign | TypeAlias
    """The actual AST node associated with this assignment statement,
    which can be an annotated assignment,
    a simple assignment, or a type alias from the `ast` module."""


@dataclass(repr=False)
class Module(Node):
    """Represents a module in the Abstract Syntax Tree (AST).

    This class is a specialized representation of a module within the AST.
    It inherits from the `Node` class and includes additional attributes
    specific to module representations.

    This class is intended to encapsulate the details of module nodes within
    the AST, allowing for easier manipulation and analysis of module-related
    information in Python code.
    """

    node: ast.Module
    """The actual AST node associated with this module, representing the entire
    module structure as defined in the Abstract Syntax Tree (AST) from the
    `ast` module."""


def iter_child_nodes(node: AST, module: str) -> Iterator[Object | Import]:
    """Iterates over the child nodes of the given AST node.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    yield child nodes that are either `Object` or `Import` instances. It uses
    the `mkapi.ast` module to iterate over the child nodes of the provided
    AST node.

    Args:
        node (AST): The root AST node to start iteration from.
        module (str): The module in which the node is defined.

    Yields:
        Object | Import: An iterator over the child nodes.

    This function is intended to be used for traversing the AST and processing
    child nodes of the given root node. It ensures that only relevant nodes
    (i.e., `Object` or `Import`) are yielded, allowing for further analysis
    or manipulation of the AST.
    """
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import):
            for name, fullname in _iter_imports(child):
                yield Import(name, child, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_imports_from_star(child, module)

            else:
                it = _iter_imports_from(child, module)
                for name, fullname in it:
                    yield Import(name, child, fullname)

        elif isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield Definition(child.name, child, module)

        elif is_assign(child) and (name := get_assign_name(child)):
            yield Assign(name, child, module)


def _iter_imports(node: ast.Import) -> Iterator[tuple[str, str]]:
    """Iterates over the imports in the given import node.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    yield tuples of the alias name and the full name of the imported module
    or attribute. It uses the `ast` module to iterate over the import names
    in the provided import node.

    Args:
        node (ast.Import): The import node to iterate over.

    Yields:
        tuple[str, str]: An iterator over the alias name and the full name
            of the imported module or attribute.

    This function is intended to be used for traversing the AST and processing
    import-related information in Python code. It ensures that only relevant
    information (i.e., alias name and full name) is yielded, allowing for
    further analysis or manipulation of the AST.
    """
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_attribute_names(alias.name):
                yield module_name, module_name


def _get_module(node: ast.ImportFrom, module: str) -> str:
    """Gets the module name from the given import from node.

    This function is designed to extract the module name from the given
    import from node. It uses the `ast` module to determine the module name
    based on the node's level and module attributes.

    Args:
        node (ast.ImportFrom): The import from node to process.
        module (str): The module in which the node is defined.

    Returns:
        str: The module name extracted from the import from node.

    This function is intended to be used for extracting the module name from
    an import from node, allowing for further analysis or manipulation of
    the AST. It ensures that the module name is correctly formatted based
    on the node's level and module attributes.
    """
    if not node.level and node.module:
        return node.module

    names = module.split(".")

    if is_package(module):
        prefix = ".".join(names[: len(names) - node.level + 1])

    else:
        prefix = ".".join(names[: -node.level])

    return f"{prefix}.{node.module}" if node.module else prefix


def _iter_imports_from(node: ast.ImportFrom, module: str) -> Iterator[tuple[str, str]]:
    """Iterates over the imports from the given import from node.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    yield tuples of the alias name and the full name of the imported module
    or attribute. It uses the `ast` module to iterate over the import names
    in the provided import from node.

    Args:
        node (ast.ImportFrom): The import from node to iterate over.
        module (str): The module in which the node is defined.

    Yields:
        tuple[str, str]: An iterator over the alias name and the full name
            of the imported module or attribute.

    This function is intended to be used for traversing the AST and processing
    import-related information in Python code. It ensures that only relevant
    information (i.e., alias name and full name) is yielded, allowing for
    further analysis or manipulation of the AST.
    """
    module = _get_module(node, module)

    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_imports_from_star(
    node: ast.ImportFrom,
    module: str,
) -> Iterator[Object | Import]:
    """Iterates over the imports from the given import from node.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    yield tuples of the alias name and the full name of the imported module
    or attribute. It uses the `ast` module to iterate over the import names
    in the provided import from node.

    Args:
        node (ast.ImportFrom): The import from node to iterate over.
        module (str): The module in which the node is defined.

    Yields:
        Object | Import: An iterator over the child nodes.

    This function is intended to be used for traversing the AST and processing
    child nodes of the given root node. It ensures that only relevant nodes
    (i.e., `Object` or `Import`) are yielded, allowing for further analysis
    or manipulation of the AST.
    """
    module = _get_module(node, module)

    if not (node_ := get_module_node(module)):
        return

    names = list_exported_names(module)

    for child in iter_child_nodes(node_, module):
        if child.name.startswith("_"):
            continue

        if not names or child.name in names:
            yield child


@cache
def get_child_nodes(node: AST, module: str) -> list[Object | Import]:
    """Gets the child nodes of the given AST node.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    collect child nodes of the given root node. It uses the `iter_child_nodes`
    function to iterate over the child nodes of the provided AST node.

    Args:
        node (AST): The root AST node to start iteration from.
        module (str): The module in which the node is defined.

    Returns:
        list[Object | Import]: A list of child nodes.

    This function is intended to be used for collecting child nodes of the
    given root node, allowing for further analysis or manipulation of the
    AST. It ensures that only relevant nodes (i.e., `Object` or `Import`)
    are collected, allowing for easier access to the relevant information
    in the AST.
    """
    node_dict: dict[str, list[Object | Import]] = {}

    for child in iter_child_nodes(node, module):
        if child.name not in node_dict:
            node_dict[child.name] = [child]

        else:
            nodes = node_dict[child.name]
            if not isinstance(nodes[-1], Definition) or not isinstance(
                child, Definition
            ):
                nodes.clear()

            nodes.append(child)

    return list(chain(*node_dict.values()))


def iter_nodes(fullname: str) -> Iterator[Module | Object | Import]:
    """Iterates over the nodes in the given full name.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    yield nodes that are either `Module`, `Object`, or `Import` instances.
    It uses the `get_module_node` function to get the module node and the
    `get_child_nodes` function to iterate over the child nodes of the
    provided module node.

    Args:
        fullname (str): The fully qualified name of the module or object.

    Yields:
        Module | Object | Import: An iterator over the nodes.

    This function is intended to be used for traversing the AST and processing
    nodes of the given full name, allowing for further analysis or manipulation
    of the AST. It ensures that only relevant nodes (i.e., `Module`, `Object`,
    or `Import`) are yielded, allowing for easier access to the relevant
    information in the AST.
    """
    if node := get_module_node(fullname):
        yield Module(fullname, node)
        return

    if "." not in fullname:
        return

    module, name = fullname.rsplit(".", maxsplit=1)

    if not (node := get_module_node(module)):
        return

    for child in get_child_nodes(node, module):
        if child.name == name:
            if isinstance(child, Import) and child.fullname != fullname:
                yield from iter_nodes(child.fullname)

            else:
                yield child


@cache
def parse(node: AST, module: str) -> list[tuple[str, Module | Object | Import]]:
    """Parses the given AST node and returns a list of tuples.

    This function is designed to traverse the Abstract Syntax Tree (AST) and
    return a list of tuples containing the name and the corresponding node.
    It uses the `get_child_nodes` function to get the child nodes of the
    provided AST node and the `iter_nodes` function to iterate over the nodes
    in the given full name.

    Args:
        node (AST): The root AST node to start iteration from.
        module (str): The module in which the node is defined.

    Returns:
        list[tuple[str, Module | Object | Import]]: A list of tuples
            containing the name and the corresponding node.

    This function is intended to be used for parsing the AST and collecting
    relevant information about the nodes in the given full name. It ensures
    that only relevant nodes (i.e., `Module`, `Object`, or `Import`) are
    collected, allowing for easier access to the relevant information in
    the AST.
    """
    children = []

    for child in get_child_nodes(node, module):
        if isinstance(child, Import) and (nodes := list(iter_nodes(child.fullname))):
            children.extend((child.name, node) for node in nodes)

        else:
            children.append((child.name, child))

    return children


@cache
def resolve(
    name: str, module: str | None = None
) -> tuple[str | None, str | None] | None:
    """Resolves the given name and returns a tuple of the name and module.

    This function is designed to resolve the given name and return a tuple
    containing the name and module. It uses the `get_module_node` function
    to get the module node and the `parse` function to iterate over the nodes
    in the given full name.

    Args:
        name (str): The name to resolve.
        module (str | None): The module in which the name is defined.

    Returns:
        tuple[str | None, str | None] | None: A tuple containing the name
            and module, or None if the name could not be resolved.

    This function is intended to be used for resolving the given name and
    returning the corresponding name and module. It ensures that the name
    and module are correctly formatted and that the name is resolved within
    the given module context.
    """
    if not module:
        if not (name_module := split_module_name(name)):
            return None

        name, module = name_module
        if not module:
            return name, None

    if not (node := get_module_node(module)):
        return None

    names = name.split(".")
    for name_, obj in parse(node, module):
        if name_ == names[0]:
            if isinstance(obj, Import):
                return None, obj.fullname

            qualname = ".".join([obj.name, *names[1:]])
            if isinstance(obj, Module):
                return resolve(qualname)

            if isinstance(obj, Object):
                if len(names) == 1:
                    return qualname, obj.module

                for child in get_child_nodes(obj.node, obj.module):
                    if child.name == names[1]:
                        return qualname, obj.module

                return None

    if get_object_from_module(name, module):
        return name, module

    return None


@cache
def get_fullname(name: str, module: str | None = None) -> str | None:
    """Gets the full name of the given name and module.

    This function is designed to get the full name of the given name and module.
    It uses the `resolve` function to resolve the given name and module.

    Args:
        name (str): The name to get the full name of.
        module (str | None): The module in which the name is defined.

    Returns:
        str | None: The full name of the given name and module, or None if the
            name could not be resolved.

    This function is intended to be used for getting the full name of the
    given name and module. It ensures that the name and module are correctly
    formatted and that the name is resolved within the given module context.
    """
    if not (name_module := resolve(name, module)):
        return None

    name_, module = name_module

    if not module:
        return name_

    if not name_:
        return module

    return f"{module}.{name_}"
