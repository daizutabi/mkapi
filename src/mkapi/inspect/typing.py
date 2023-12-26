"""Type string."""
import inspect
from types import EllipsisType, NoneType, UnionType
from typing import ForwardRef, Union, get_args, get_origin

from mkapi.core.link import get_link


def type_string_none(tp: NoneType, obj: object) -> str:  # noqa: D103, ARG001
    return ""


def type_string_ellipsis(tp: EllipsisType, obj: object) -> str:  # noqa: D103, ARG001
    return "..."


def type_string_union(tp: UnionType, obj: object) -> str:  # noqa: D103
    return " | ".join(type_string(arg, obj=obj) for arg in get_args(tp))


def type_string_list(tp: list, obj: object) -> str:  # noqa: D103
    args = ", ".join(type_string(arg, obj=obj) for arg in tp)
    return f"[{args}]"


def type_string_str(tp: str, obj: object) -> str:
    """Return a resolved name for `str`.

    Examples:
        >>> from mkapi.core.base import Docstring
        >>> type_string_str("Docstring", Docstring)
        '[Docstring](!mkapi.core.base.Docstring)'
        >>> type_string_str("invalid_object_name", Docstring)
        'invalid_object_name'
        >>> type_string_str("no_module", 1)
        'no_module'
    """
    if module := inspect.getmodule(obj):  # noqa: SIM102
        if type_ := dict(inspect.getmembers(module)).get(tp):
            return type_string(type_)
    return tp


def type_string_forward_ref(tp: ForwardRef, obj: object) -> str:  # noqa: D103
    return type_string_str(tp.__forward_arg__, obj)


TYPE_STRING_FUNCTIONS = {
    NoneType: type_string_none,
    EllipsisType: type_string_ellipsis,
    UnionType: type_string_union,
    list: type_string_list,
    str: type_string_str,
    ForwardRef: type_string_forward_ref,
}


def register_type_string_function(type_, func) -> None:  # noqa: ANN001, D103
    TYPE_STRING_FUNCTIONS[type_] = func


def type_string(tp, *, kind: str = "returns", obj: object = None) -> str:  # noqa: ANN001
    """Return string expression for type.

    If possible, type string includes link.

    Args:
        tp: type
        kind: 'returns' or 'yields'
        obj: Object

    Examples:
        >>> type_string(str)
        'str'
        >>> from mkapi.core.node import Node
        >>> type_string(Node)
        '[Node](!mkapi.core.node.Node)'
        >>> type_string(None)
        ''
        >>> type_string(...)
        '...'
        >>> type_string([int, str])
        '[int, str]'
        >>> type_string(int | str)
        'int | str'
        >>> type_string("Node", obj=Node)
        '[Node](!mkapi.core.node.Node)'
        >>> from typing import List
        >>> type_string(List["Node"], obj=Node)
        'list[[Node](!mkapi.core.node.Node)]'
        >>> from collections.abc import Iterable
        >>> type_string(Iterable[int], kind="yields")
        'int'
    """
    if kind == "yields":
        return type_string_yields(tp, obj)
    for type_, func in TYPE_STRING_FUNCTIONS.items():
        if isinstance(tp, type_):
            return func(tp, obj)
    if isinstance(tp, type):
        return get_link(tp)
    if get_origin(tp):
        return type_string_origin_args(tp, obj)
    raise NotImplementedError


def type_string_origin_args(tp, obj: object = None) -> str:  # noqa: ANN001
    """Return string expression for X[Y, Z, ...].

    Args:
        tp: type
        obj: Object

    Examples:
        >>> type_string_origin_args(list[str])
        'list[str]'
        >>> from typing import List, Tuple
        >>> type_string_origin_args(List[Tuple[int, str]])
        'list[tuple[int, str]]'
        >>> from mkapi.core.node import Node
        >>> type_string_origin_args(list[Node])
        'list[[Node](!mkapi.core.node.Node)]'
        >>> from collections.abc import Callable, Iterator
        >>> type_string_origin_args(Iterator[float])
        '[Iterator](!collections.abc.Iterator)[float]'
        >>> type_string_origin_args(Callable[[], str])
        '[Callable](!collections.abc.Callable)[[], str]'
        >>> from typing import Union, Optional
        >>> type_string_origin_args(Union[int, str])
        'int | str'
        >>> type_string_origin_args(Optional[bool])
        'bool | None'

    """
    origin, args = get_origin(tp), get_args(tp)
    args_list = [type_string(arg, obj=obj) for arg in args]
    if origin is Union:
        if len(args) == 2 and args[1] == type(None):  # noqa: PLR2004
            return f"{args_list[0]} | None"
        return " | ".join(args_list)
    origin_str = type_string(origin, obj=obj)
    args_str = ", ".join(args_list)
    return f"{origin_str}[{args_str}]"


def type_string_yields(tp, obj: object) -> str:  # noqa: ANN001
    """Return string expression for type in generator.

    Examples:
        >>> from collections.abc import Iterator
        >>> type_string_yields(Iterator[int], None)
        'int'
        >>> type_string_yields(int, None)  # invalid type
        ''
        >>> type_string_yields(list[str, float], None)  # invalid type
        'list[str, float]'
    """
    if args := get_args(tp):
        if len(args) == 1:
            return type_string(args[0], obj=obj)
        return type_string(tp, obj=obj)
    return ""
