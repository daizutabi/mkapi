"""Provide utilities for working with Abstract Syntax Trees (AST).

Include functions and classes for analyzing, transforming, and
manipulating AST nodes, which represent the structure of Python code.

Key Features:
- Identification of various node types, such as function definitions,
  class definitions, assignments, and decorators.
- Utilities for renaming nodes and transforming AST structures.
- Functions to extract identifiers and analyze function signatures.
- Support for decorators, including properties, class methods, and static methods.
"""

from __future__ import annotations

import ast
import re
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    Name,
    NodeTransformer,
    Raise,
)
from dataclasses import dataclass
from inspect import Parameter as P
from inspect import cleandoc
from typing import TYPE_CHECKING, TypeGuard

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable, Iterator
    from inspect import _ParameterKind


def iter_child_nodes(node: AST) -> Iterator[AST]:
    """Yield child nodes of the given AST node.

    Traverse the child nodes of the specified Abstract Syntax
    Tree (AST) node and yield each child node that is of interest, including
    import statements, class definitions, and function definitions.
    Allow recursive traversal of the AST structure.

    Args:
        node (AST): The AST node from which to yield child nodes.

    Yields:
        AST: The child nodes of the specified AST node.

    Examples:
        >>> import ast
        >>> tree = ast.parse("def foo(): pass")
        >>> for child in iter_child_nodes(tree):
        ...     print(type(child))
        <class 'ast.FunctionDef'>
    """
    it = ast.iter_child_nodes(node)

    for child in it:
        if isinstance(
            child, Import | ImportFrom | ClassDef | FunctionDef | AsyncFunctionDef
        ):
            yield child

        elif isinstance(child, AnnAssign | Assign | TypeAlias):
            yield from _iter_assign_nodes(child, it)

        else:
            yield from iter_child_nodes(child)


def _get_pseudo_docstring(node: AST) -> str | None:
    """Retrieve the pseudo docstring from an AST node.

    Check if the given Abstract Syntax Tree (AST) node is an
    expression containing a constant value. If the constant value is a string
    that starts with the pseudo docstring marker (i.e., '#:'), return the
    cleaned-up version of the docstring. If the node does not contain a valid
    pseudo docstring, return None.

    Args:
        node (AST): The AST node to inspect for a pseudo docstring.

    Returns:
        str | None: The cleaned pseudo docstring if found, otherwise None.
    """
    if isinstance(node, Expr) and isinstance(node.value, Constant):
        doc = node.value.value
        return cleandoc(doc) if isinstance(doc, str) else None

    return None


def _iter_assign_nodes(
    node: AnnAssign | Assign | TypeAlias,  # type: ignore
    it: Iterator[AST],
) -> Iterator[AST]:
    """Yield assignment nodes from the given AST node.

    Recursively yield assignment nodes (AnnAssign, Assign,
    or TypeAlias) from the provided Abstract Syntax Tree (AST) node.
    Process the current node and its subsequent nodes in the iterator,
    yield each relevant assignment node until a non-assignment node is
    encountered.

    Args:
        node (AnnAssign | Assign | TypeAlias): The initial assignment node
            to process.
        it (Iterator[AST]): An iterator over the child nodes of the AST.

    Yields:
        AST: The assignment nodes found in the AST.
    """
    node.__doc__ = None

    try:
        next_node = next(it)
    except StopIteration:
        yield node
        return

    if isinstance(next_node, AnnAssign | Assign | TypeAlias):
        yield node
        yield from _iter_assign_nodes(next_node, it)

    elif isinstance(next_node, FunctionDef | AsyncFunctionDef | ClassDef):
        yield node
        yield next_node

    else:
        node.__doc__ = _get_pseudo_docstring(next_node)
        yield node


def get_assign_name(node: AnnAssign | Assign | TypeAlias) -> str | None:  # type: ignore
    """Return the name of the assign node.

    Retrieve the name associated with an assignment node,
    which can be of type AnnAssign, Assign, or TypeAlias.
    Handle different types of assignment nodes and return the name as a string.
    If the node does not represent a valid assignment, return None.

    Args:
        node (AnnAssign | Assign | TypeAlias): The assignment node from
            which to extract the name.

    Returns:
        str | None: The name of the assignment node if found, otherwise None.

    Examples:
        >>> import ast
        >>> node = ast.parse("x = 1").body[0]
        >>> get_assign_name(node)
        'x'
        >>> node = ast.parse("y: int = 2").body[0]
        >>> get_assign_name(node)
        'y'
    """
    if isinstance(node, Assign):
        name = node.targets[0]

    elif isinstance(node, AnnAssign):
        name = node.target

    elif TypeAlias and isinstance(node, TypeAlias):
        name = node.name

    else:
        return None

    if isinstance(name, Name | Attribute):
        return ast.unparse(name)

    return None


def get_assign_type(node: AnnAssign | Assign | TypeAlias) -> ast.expr | None:  # type: ignore
    """Return the type annotation of the Assign or TypeAlias AST node.

    Retrieve the type annotation associated with an assignment
    node, which can be of type AnnAssign, Assign, or TypeAlias.
    Check the node type and return the corresponding type annotation if available.
    If the node does not represent a valid assignment or does not have a type
    annotation, return None.

    Args:
        node (AnnAssign | Assign | TypeAlias): The assignment node from which
            to extract the type annotation.

    Returns:
        ast.expr | None: The type annotation of the assignment node if found,
            otherwise None.

    Examples:
        >>> import ast
        >>> node = ast.parse("x: int = 1").body[0]
        >>> get_assign_type(node)  # doctest: +ELLIPSIS
        <ast.Name object at 0x...>
        >>> node = ast.parse("y = 2").body[0]
        >>> get_assign_type(node) is None
        True
    """
    if isinstance(node, AnnAssign):
        return node.annotation

    if TypeAlias and isinstance(node, TypeAlias):
        return node.value

    return None


def _iter_parameters(
    node: FunctionDef | AsyncFunctionDef,
) -> Iterator[tuple[str, ast.expr | None, _ParameterKind]]:
    """Yield parameters from a function definition node.

    Extract and yield the parameters of a function definition
    node, which can be either a synchronous or asynchronous function.
    Process positional-only arguments, positional-or-keyword arguments,
    variable positional arguments, keyword-only arguments, and variable
    keyword arguments, yielding each parameter along with its type annotation
    and kind.

    Args:
        node (FunctionDef | AsyncFunctionDef): The function definition node
            from which to extract parameters.

    Yields:
        tuple[str, ast.expr | None, _ParameterKind]: A tuple containing the
        parameter name, its type annotation (if any), and its kind (e.g.,
        positional-only, positional-or-keyword, keyword-only, or variable).

    Examples:
        >>> import ast
        >>> src = "def func(a, b: int, *args, c: str, d=5, **kwargs): pass"
        >>> node = ast.parse(src).body[0]
        >>> args = list(_iter_parameters(node))
        >>> args[0]
        ('a', None, <_ParameterKind.POSITIONAL_OR_KEYWORD: 1>)
        >>> args[1]  # doctest: +ELLIPSIS
        ('b', <ast.Name object at 0x...>, <_ParameterKind.POSITIONAL_OR_KEYWORD: 1>)
        >>> args[2]  # doctest: +ELLIPSIS
        ('args', None, <_ParameterKind.VAR_POSITIONAL: 2>)
        >>> args[3]  # doctest: +ELLIPSIS
        ('c', <ast.Name object at 0x...>, <_ParameterKind.KEYWORD_ONLY: 3>)
        >>> args[4]
        ('d', None, <_ParameterKind.KEYWORD_ONLY: 3>)
    """
    args = node.args
    for arg in args.posonlyargs:
        yield arg.arg, arg.annotation, P.POSITIONAL_ONLY
    for arg in args.args:
        yield arg.arg, arg.annotation, P.POSITIONAL_OR_KEYWORD
    if arg := args.vararg:
        yield arg.arg, arg.annotation, P.VAR_POSITIONAL
    for arg in args.kwonlyargs:
        yield arg.arg, arg.annotation, P.KEYWORD_ONLY
    if arg := args.kwarg:
        yield arg.arg, arg.annotation, P.VAR_KEYWORD


def _iter_defaults(node: FunctionDef | AsyncFunctionDef) -> Iterator[ast.expr | None]:
    """Yield default values for parameters in a function definition node.

    Extract and yield the default values for parameters
    defined in a function definition node, which can be either a synchronous
    or asynchronous function. Process both positional and keyword
    arguments, yielding the default values in the order they are defined.

    Args:
        node (FunctionDef | AsyncFunctionDef): The function definition node
            from which to extract default values.

    Yields:
        ast.expr | None: The default values for the parameters, or None
        for parameters that do not have a default value.

    Examples:
        >>> import ast
        >>> src = "def func(a, b=2, c=3): pass"
        >>> node = ast.parse(src).body[0]
        >>> list(_iter_defaults(node))  # doctest: +ELLIPSIS
        [None, <ast.Constant object at 0x...>, <ast.Constant object at 0x...>]
    """
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional

    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


@dataclass
class Parameter:
    """Represent a parameter in a function or method.

    Encapsulate the details of a parameter, including its name,
    type annotation, default value, and kind. It is used to provide a structured
    representation of function parameters, making it easier to analyze and manipulate
    function signatures.

    Attributes:
        name (str): The name of the parameter.
        type (ast.expr | None): The type annotation of the parameter, represented
            as an AST expression. This can be None if no type annotation is provided.
        default (ast.expr | None): The default value of the parameter, represented
            as an AST expression. This can be None if the parameter does not have
            a default value.
        kind (_ParameterKind): The kind of the parameter, indicating whether it is
            positional-only, positional-or-keyword, keyword-only, or variable.

    Examples:
        >>> from mkapi.ast import FunctionDef
        >>> param = Parameter(name="arg1", type=None, default=None, kind=P.POSITIONAL_OR_KEYWORD)
        >>> param.name
        'arg1'
        >>> param.type is None
        True
        >>> param.default is None
        True
        >>> param.kind
        <_ParameterKind.POSITIONAL_OR_KEYWORD: 1>
    """

    name: str
    type: ast.expr | None  # noqa: A003, RUF100
    default: ast.expr | None
    kind: _ParameterKind

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


def iter_parameters(node: FunctionDef | AsyncFunctionDef) -> Iterator[Parameter]:
    """Yield `Parameter` instances from a function node.

    Extract parameters from a function definition node, which can
    be either a synchronous or asynchronous function. Utilize the helper
    function `_iter_parameters` to retrieve the parameter names, type annotations,
    and kinds. Additionally, use `_iter_defaults` to obtain the default values
    for parameters that have them. The function yields instances of the `Parameter`
    class, encapsulating the details of each parameter.

    Args:
        node (FunctionDef | AsyncFunctionDef): The function definition node
            from which to extract parameters.

    Yields:
        Parameter: An instance of the `Parameter` class for each parameter
        defined in the function, containing the name, type annotation, default
        value (if any), and kind.

    Examples:
        >>> import ast
        >>> src = "def func(a, b: int, *args, c: str, d=5, **kwargs): pass"
        >>> node = ast.parse(src).body[0]
        >>> params = list(iter_parameters(node))
        >>> params[0].name
        'a'
        >>> params[1].type.id
        'int'
        >>> params[1].default is None
        True
        >>> params[4].default.value
        5
    """
    it = _iter_defaults(node)
    for name, type_, kind in _iter_parameters(node):
        default = None if kind in [P.VAR_POSITIONAL, P.VAR_KEYWORD] else next(it)
        yield Parameter(name, type_, default, kind)


def iter_raises(node: FunctionDef | AsyncFunctionDef) -> Iterator[ast.expr]:
    """Yield unique raises from a function node.

    Traverse the Abstract Syntax Tree (AST) of a function
    definition node, which can be either synchronous or asynchronous.
    Identify and yield unique exception types that are raised within the
    function. The function checks for `Raise` statements and extracts the
    exception type, ensuring that each type is yielded only once.

    Args:
        node (FunctionDef | AsyncFunctionDef): The function definition node
            from which to extract raised exceptions.

    Yields:
        ast.expr: The unique exception types raised within the function.

    Examples:
        >>> import ast
        >>> src = "def func(): raise ValueError('error')"
        >>> node = ast.parse(src).body[0]
        >>> raises = list(iter_raises(node))
        >>> len(raises)
        1
        >>> ast.unparse(raises[0])
        'ValueError'
    """
    names = []
    for child in ast.walk(node):
        if isinstance(child, Raise) and (type_ := child.exc):
            if isinstance(type_, Call):
                type_ = type_.func

            name = ast.unparse(type_)
            if name not in names:
                yield type_
                names.append(name)


# a1.b_2(c[d]) -> a1, b_2, c, d
SPLIT_IDENTIFIER_PATTERN = re.compile(r"[\.\[\]\(\)|]|\s+")


def _split_name(name: str) -> list[str]:
    return [x for x in re.split(SPLIT_IDENTIFIER_PATTERN, name) if x]


def _is_identifier(name: str) -> bool:
    return name != "" and all(x.isidentifier() for x in _split_name(name))


def create_ast_expr(name: str) -> ast.expr:
    """Return an [ast.expr] instance of a name.

    Create and return an Abstract Syntax Tree (AST) expression
    representing the given name. First, check if the name is a valid
    identifier. If it is, attempt to parse the name into an AST
    node. If the parsing is successful and the resulting node is an expression,
    return the value of that expression. If the name is not a
    valid identifier or if a SyntaxError occurs during parsing, return a
    Constant expression with an empty string.

    Args:
        name (str): The name to convert into an AST expression.

    Returns:
        ast.expr: An AST expression representing the name, or a Constant
        expression if the name is invalid or cannot be parsed.

    Examples:
        >>> create_ast_expr("x").id
        'x'
        >>> create_ast_expr("invalid name").value
        ''
        >>> create_ast_expr("42").value
        '42'
    """
    if _is_identifier(name):
        try:
            expr = ast.parse(name).body[0]
        except SyntaxError:
            return Constant("")

        if isinstance(expr, Expr):
            return expr.value

    return Constant(value=name)


PREFIX = "__mkapi__."


class Transformer(NodeTransformer):
    """AST Transformer for Renaming Nodes.

    Extend the `NodeTransformer` to provide functionality for
    renaming Abstract Syntax Tree (AST) nodes. Traverse the
    AST and modify specific nodes according to the renaming rules defined
    within the class. The primary purpose of this transformer is to prepend
    the specified prefix (`__mkapi__.`) to the names of nodes, allowing
    for systematic renaming during AST transformations.

    Examples:
        >>> transformer = Transformer()
        >>> node = ast.parse("x = 1")
        >>> transformer.unparse(node)
        '__mkapi__.x = 1'
    """

    def _rename(self, name: str) -> Name:
        return Name(id=f"{PREFIX}{name}")

    def visit_Name(self, node: Name) -> Name:  # noqa: N802
        return self._rename(node.id)

    def unparse(self, node: AST) -> str:
        """Convert the transformed AST node back into source code.

        Take an Abstract Syntax Tree (AST) node, apply the
        transformations defined in the `visit` methods of the transformer,
        and return the corresponding source code as a string. To avoid
        in-place renaming, it first creates a copy of the node by parsing
        the unparsed version of the original node.

        Args:
            node (AST): The AST node to be transformed and converted back
                into source code.

        Returns:
            str: The source code representation of the transformed AST node.

        Examples:
            >>> transformer = Transformer()
            >>> node = ast.parse("a.b.c")
            >>> transformer.unparse(node)
            '__mkapi__.a.b.c'
        """
        # copy node for avoiding in-place rename.
        node_ = ast.parse(ast.unparse(node))
        return ast.unparse(self.visit(node_))


class StringTransformer(Transformer):
    """AST Transformer for renaming string constants.

    Extend the `Transformer` to provide functionality for
    renaming string constant nodes in the Abstract Syntax Tree (AST).
    Traverse the AST and modify `Constant` nodes that contain
    string values by renaming them according to the rules defined in the
    parent class.
    """

    def visit_Constant(self, node: Constant) -> Constant | Name:  # noqa: N802
        """
        Visit a `Constant` node and rename it if its value is a string.

        Override the `visit_Constant` method from the `Transformer`
        class. Check if the value of the `Constant` node is a string,
        and if so, rename the string using the `_rename` method. If the
        value is not a string, return the node unchanged.

        Args:
            node (Constant): The `Constant` node to be visited and potentially renamed.

        Returns:
            Constant | Name: The renamed `Constant` node if its value is a string,
            otherwise the original `Constant` node.

        Examples:
            >>> transformer = StringTransformer()
            >>> node = ast.parse('"hello"')
            >>> transformer.unparse(node)
            '__mkapi__.hello'
        """
        if isinstance(node.value, str):
            return self._rename(node.value)

        return node


def _iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers as a tuple of (code, is_valid_identifier).

    Scan the provided source string for segments that may
    represent identifiers, particularly those prefixed with a specific
    string defined by the `PREFIX` constant. Yield tuples containing
    the code segment and a boolean indicating whether the segment is a
    valid identifier according to Python's identifier rules. Continue to
    search through the source string until all segments have been processed.

    Args:
        source (str): The source string to scan for identifiers.

    Yields:
        tuple[str, bool]: A tuple where the first element is a code segment
        and the second element is a boolean indicating if the segment is a
        valid Python identifier.

    Examples:
        >>> x = list(_iter_identifiers("x, __mkapi__.a.b0[__mkapi__.c], y"))
        >>> x[0]
        ('x, ', False)
        >>> x[1]
        ('a.b0', True)
        >>> x[2]
        ('[', False)
        >>> x[3]
        ('c', True)
        >>> x[4]
        ('], y', False)
    """
    start = 0
    while start < len(source):
        index = source.find(PREFIX, start)

        if index == -1:
            yield source[start:], False
            return

        if index != 0:
            yield source[start:index], False

        start = stop = index + len(PREFIX)

        while stop < len(source):
            c = source[stop]
            if c == "." or c.isdigit() or c.isidentifier():
                stop += 1

            else:
                break

        yield source[start:stop], True
        start = stop


def iter_identifiers(node: AST) -> Iterator[str]:
    """Yield identifiers from an AST node.

    Extract identifiers from the given Abstract Syntax Tree (AST)
    node by first converting the node back into source code using the
    `StringTransformer`. Scan the resulting source code for segments
    that may represent valid Python identifiers. Only valid identifiers are
    yielded.

    Args:
        node (AST): The AST node from which to extract identifiers.

    Yields:
        str: Each valid identifier found in the AST node's source code.

    Examples:
        >>> import ast
        >>> src = "'a[b]'"
        >>> node = ast.parse(src)
        >>> identifiers = list(iter_identifiers(node))
        >>> identifiers
        ['a']
    """
    source = StringTransformer().unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield code


def _unparse(
    node: AST, callback: Callable[[str], str], *, is_type: bool = True
) -> Iterator[str]:
    trans = StringTransformer() if is_type else Transformer()
    source = trans.unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield callback(code)

        else:
            yield code


def unparse(node: AST, callback: Callable[[str], str], *, is_type: bool = True) -> str:
    """Unparse the AST node with a callback function.

    Take an Abstract Syntax Tree (AST) node and a callback
    function, and convert the AST node back into source code.
    The callback function is applied to each identifier found in the AST,
    allowing for custom transformations of the identifiers during the
    unparse process. The `is_type` parameter determines whether the
    transformation is for type-related nodes or general nodes.

    Args:
        node (AST): The AST node to be converted back into source code.
        callback (Callable[[str], str]): A function that takes a string
            (identifier) and returns a transformed string.
        is_type (bool, optional): A flag indicating whether the transformation
            is for type-related nodes. Defaults to True.

    Returns:
        str: The source code representation of the unparsed AST node.

    Examples:
        >>> def transform(identifier: str) -> str:
        ...     return f"<{identifier}>"
        >>> src = "a + b"
        >>> node = ast.parse(src)
        >>> unparse(node, transform)
        '<a> + <b>'
    """
    return "".join(_unparse(node, callback, is_type=is_type))


def has_decorator(node: AST, name: str, index: int = 0) -> bool:
    """Check if a class or function has a specific decorator.

    Check whether the given Abstract Syntax Tree (AST) node,
    which can be a class definition or a function definition (synchronous or
    asynchronous), has a decorator with the specified name.
    Traverse the decorator list of the node and compare the names of the
    decorators to the provided name. The `index` parameter allows for
    checking decorators at a specific position in the decorator list.

    Args:
        node (AST): The AST node to inspect for decorators.
        name (str): The name of the decorator to check for.
        index (int, optional): The index of the decorator in the list to check.
            Defaults to 0, which checks for the first decorator.

    Returns:
        bool: True if the specified decorator is found at the given index,
        False otherwise.

    Examples:
        >>> import ast
        >>> src = "@my_decorator\\ndef func():\\n pass"
        >>> node = ast.parse(src).body[0]
        >>> has_decorator(node, "my_decorator")
        True
        >>> has_decorator(node, "other_decorator")
        False
    """
    if not isinstance(node, ClassDef | FunctionDef | AsyncFunctionDef):
        return False

    for deco in node.decorator_list:
        deco_names = next(iter_identifiers(deco)).split(".")

        if len(deco_names) == index + 1 and deco_names[index] == name:
            return True

    return False


def is_function_def(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node is a function definition.

    Determine whether the given Abstract Syntax Tree (AST)
    node is a function definition, which can be either a synchronous or
    asynchronous function.

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is a function definition, otherwise False.

    Examples:
        >>> import ast
        >>> src = "def func(): pass"
        >>> node = ast.parse(src).body[0]
        >>> is_function_def(node)
        True
    """
    return isinstance(node, FunctionDef | AsyncFunctionDef)


def is_property(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node is a property.

    Determine whether the given AST node is a function definition
    and has a decorator named "property".

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is a property, otherwise False.

    Examples:
        >>> import ast
        >>> src = "@property\\ndef func(self): pass"
        >>> node = ast.parse(src).body[0]
        >>> is_property(node)
        True
    """
    return is_function_def(node) and has_decorator(node, "property")


def is_setter(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node is a setter.

    Determine whether the given AST node is a function definition
    and has a decorator named "setter" at the specified index.

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is a setter, otherwise False.

    Examples:
        >>> import ast
        >>> src = "@func.setter\\ndef func(self, value): pass"
        >>> node = ast.parse(src).body[0]
        >>> is_setter(node)
        True
    """
    return is_function_def(node) and has_decorator(node, "setter", 1)


def has_overload(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node has an overload decorator.

    Determine whether the given Abstract Syntax Tree (AST) node
    is a function definition and has a decorator named "overload".

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node has an overload decorator, otherwise False.

    Examples:
        >>> import ast
        >>> src = "@overload\\ndef func(self): pass"
        >>> node = ast.parse(src).body[0]
        >>> has_overload(node)
        True
    """
    return is_function_def(node) and has_decorator(node, "overload")


def is_function(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node is a regular function definition.

    Determine whether the given Abstract Syntax Tree (AST)
    node is a function definition and ensures that it is not a property,
    setter, or overload.

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is a regular function definition, otherwise False.

    Examples:
        >>> import ast
        >>> src = "def func(): pass"
        >>> node = ast.parse(src).body[0]
        >>> is_function(node)
        True
    """
    if not is_function_def(node):
        return False

    return not (is_property(node) or is_setter(node) or has_overload(node))


def is_classmethod(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node is a class method.

    Determine whether the given Abstract Syntax Tree (AST) node
    is a function definition and has a decorator named "classmethod".

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is a class method, otherwise False.

    Examples:
        >>> import ast
        >>> src = "@classmethod\\ndef func(cls): pass"
        >>> node = ast.parse(src).body[0]
        >>> is_classmethod(node)
        True
    """
    return is_function_def(node) and has_decorator(node, "classmethod")


def is_staticmethod(node: AST) -> TypeGuard[FunctionDef | AsyncFunctionDef]:
    """Check if the AST node is a static method.

    Determine whether the given Abstract Syntax Tree (AST) node
    is a function definition and has a decorator named "staticmethod".

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is a static method, otherwise False.

    Examples:
        >>> import ast
        >>> src = "@staticmethod\\ndef func(): pass"
        >>> node = ast.parse(src).body[0]
        >>> is_staticmethod(node)
        True
    """
    return is_function_def(node) and has_decorator(node, "staticmethod")


def is_assign(node: AST) -> TypeGuard[ast.AnnAssign | ast.Assign | TypeAlias]:  # type: ignore
    """Check if the AST node is an assignment.

    Determine whether the given Abstract Syntax Tree (AST)
    node is an assignment statement, which can be an annotated assignment,
    a regular assignment, or a type alias.

    Args:
        node (AST): The AST node to check.

    Returns:
        bool: True if the node is an assignment, otherwise False.

    Examples:
        >>> import ast
        >>> src = "x: int = 5"
        >>> node = ast.parse(src).body[0]
        >>> is_assign(node)
        True
    """
    return isinstance(node, ast.AnnAssign | ast.Assign | TypeAlias)
