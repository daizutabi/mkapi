"""Type string."""
import importlib
import inspect
from types import UnionType
from typing import ForwardRef, Union, get_args, get_origin

from mkapi.core.link import get_link


def to_string(tp, *, kind: str = "returns", obj: object = None) -> str:  # noqa: ANN001, PLR0911
    """Return string expression for type.

    If possible, type string includes link.

    Args:
        tp: type
        kind: 'returns' or 'yields'
        obj: Object

    Examples:
        >>> to_string(str)
        'str'
        >>> from mkapi.core.node import Node
        >>> to_string(Node)
        '[Node](!mkapi.core.node.Node)'
        >>> to_string(...)
        '...'
        >>> to_string([int, str])
        '[int, str]'
        >>> to_string(int | str)
        'int | str'
    """
    if kind == "yields":
        return _to_string_for_yields(tp, obj)
    if tp is None:
        return ""
    if tp == ...:
        return "..."
    if isinstance(tp, list):
        args = ", ".join(to_string(arg, obj=obj) for arg in tp)
        return f"[{args}]"
    if isinstance(tp, UnionType):
        return " | ".join(to_string(arg, obj=obj) for arg in get_args(tp))
    if isinstance(tp, str):
        return resolve_forward_ref(tp, obj)
    if isinstance(tp, ForwardRef):
        return resolve_forward_ref(tp.__forward_arg__, obj)
    if isinstance(tp, type):
        return get_link(tp)
    if get_origin(tp):
        return resolve_orign_args(tp, obj)
    raise NotImplementedError
    # if not hasattr(annotation, "__origin__"):
    #     return str(annotation).replace("typing.", "").lower()
    # origin = annotation.__origin__
    # if origin is Union:
    #     return union(annotation, obj=obj)
    # if origin is tuple:
    #     args = [to_string(x, obj=obj) for x in annotation.__args__]
    #     if args:
    #         return "(" + ", ".join(args) + ")"
    #     else:
    #         return "tuple"
    # if origin is dict:
    #     if type(annotation.__args__[0]) == TypeVar:
    #         return "dict"
    #     args = [to_string(x, obj=obj) for x in annotation.__args__]
    #     if args:
    #         return "dict(" + ": ".join(args) + ")"
    #     else:
    #         return "dict"
    # if not hasattr(annotation, "__args__"):
    #     return ""
    # if len(annotation.__args__) == 0:
    #     return annotation.__origin__.__name__.lower()
    # if len(annotation.__args__) == 1:
    #     return a_of_b(annotation, obj=obj)
    # else:
    #     return to_string_args(annotation, obj=obj)


def resolve_forward_ref(name: str, obj: object) -> str:
    """Return a resolved name for `str` or `typing.ForwardRef`.

    Args:
        name: Forward reference name.
        obj: Object

    Examples:
        >>> from mkapi.core.base import Docstring
        >>> resolve_forward_ref('Docstring', Docstring)
        '[Docstring](!mkapi.core.base.Docstring)'
        >>> resolve_forward_ref('invalid_object_name', Docstring)
        'invalid_object_name'
    """
    if obj is None or not hasattr(obj, "__module__"):
        return name
    module = importlib.import_module(obj.__module__)
    globals_ = dict(inspect.getmembers(module))
    try:
        type_ = eval(name, globals_)
    except NameError:
        return name
    else:
        return to_string(type_)


def resolve_orign_args(tp, obj: object = None) -> str:  # noqa: ANN001
    """Return string expression for X[Y, Z, ...].

    Args:
        tp: type
        obj: Object

    Examples:
        >>> resolve_orign_args(list[str])
        'list[str]'
        >>> from typing import List, Tuple
        >>> resolve_orign_args(List[Tuple[int, str]])
        'list[tuple[int, str]]'
        >>> from mkapi.core.node import Node
        >>> resolve_orign_args(list[Node])
        'list[[Node](!mkapi.core.node.Node)]'
        >>> from collections.abc import Callable, Iterator
        >>> resolve_orign_args(Iterator[float])
        '[Iterator](!collections.abc.Iterator)[float]'
        >>> resolve_orign_args(Callable[[], str])
        '[Callable](!collections.abc.Callable)[[], str]'
        >>> from typing import Union, Optional
        >>> resolve_orign_args(Union[int, str])
        'int | str'
        >>> resolve_orign_args(Optional[bool])
        'bool | None'

    """
    origin, args = get_origin(tp), get_args(tp)
    args_list = [to_string(arg, obj=obj) for arg in args]
    if origin is Union:
        if len(args) == 2 and args[1] == type(None):  # noqa: PLR2004
            return f"{args_list[0]} | None"
        return " | ".join(args_list)
    origin_str = to_string(origin, obj=obj)
    args_str = ", ".join(args_list)
    return f"{origin_str}[{args_str}]"


def _to_string_for_yields(tp, obj: object) -> str:  # noqa: ANN001
    if hasattr(tp, "__args__") and tp.__args__:
        if len(tp.__args__) == 1:
            return to_string(tp.__args__[0], obj=obj)
        return to_string(tp, obj=obj)
    return ""


# def a_of_b(annotation, obj=None) -> str:
#     """Return "A of B" style string.

#     Args:
#         annotation: Annotation

#     Examples:
#         >>> from typing import List, Iterable, Iterator
#         >>> a_of_b(List[str])
#         'list of str'
#         >>> a_of_b(List[List[str]])
#         'list of list of str'
#         >>> a_of_b(Iterable[int])
#         'iterable of int'
#         >>> a_of_b(Iterator[float])
#         'iterator of float'
#     """
#     origin = annotation.__origin__
#     if not hasattr(origin, "__name__"):
#         return ""
#     name = origin.__name__.lower()
#     if type(annotation.__args__[0]) == TypeVar:
#         return name
#     type_ = f"{name} of " + to_string(annotation.__args__[0], obj=obj)
#     if type_.endswith(" of T"):
#         return name
#     return type_


# def union(annotation, obj=None) -> str:
#     """Return a string for union annotation.

#     Args:
#         annotation: Annotation

#     Examples:
#         >>> from typing import List, Optional, Tuple, Union
#         >>> union(Optional[List[str]])
#         'list of str, optional'
#         >>> union(Union[str, int])
#         'str or int'
#         >>> union(Union[str, int, float])
#         'str, int, or float'
#         >>> union(Union[List[str], Tuple[int, int]])
#         'Union(list of str, (int, int))'
#     """
#     args = annotation.__args__
#     if (
#         len(args) == 2
#         and hasattr(args[1], "__name__")
#         and args[1].__name__ == "NoneType"
#     ):
#         return to_string(args[0], obj=obj) + ", optional"
#     else:
#         args = [to_string(x, obj=obj) for x in args]
#         if all(" " not in arg for arg in args):
#             if len(args) == 2:
#                 return " or ".join(args)
#             else:
#                 return ", ".join(args[:-1]) + ", or " + args[-1]
#         else:
#             return "Union(" + ", ".join(to_string(x, obj=obj) for x in args) + ")"


# def to_string_args(annotation, obj: object = None) -> str:
#     """Return a string for callable and generator annotation.

#     Args:
#         annotation: Annotation

#     Examples:
#         >>> from typing import Callable, List, Tuple, Any
#         >>> from typing import Generator, AsyncGenerator
#         >>> to_string_args(Callable[[int, List[str]], Tuple[int, int]])
#         'callable(int, list of str: (int, int))'
#         >>> to_string_args(Callable[[int], Any])
#         'callable(int)'
#         >>> to_string_args(Callable[[str], None])
#         'callable(str)'
#         >>> to_string_args(Callable[..., int])
#         'callable(...: int)'
#         >>> to_string_args(Generator[int, float, str])
#         'generator(int, float, str)'
#         >>> to_string_args(AsyncGenerator[int, float])
#         'asyncgenerator(int, float)'
#     """

#     def to_string_with_prefix(annotation, prefix: str = ",") -> str:
#         s = to_string(annotation, obj=obj)
#         if s in ["NoneType", "any"]:
#             return ""
#         return f"{prefix} {s}"

#     args = annotation.__args__
#     name = annotation.__origin__.__name__.lower()
#     if name == "callable":
#         *args, returns = args
#         args = ", ".join(to_string(x, obj=obj) for x in args)
#         returns = to_string_with_prefix(returns, ":")
#         return f"{name}({args}{returns})"
#     if name == "generator":
#         arg, sends, returns = args
#         arg = to_string(arg, obj=obj)
#         sends = to_string_with_prefix(sends)
#         returns = to_string_with_prefix(returns)
#         if not sends and returns:
#             sends = ","
#         return f"{name}({arg}{sends}{returns})"
#     if name == "asyncgenerator":
#         arg, sends = args
#         arg = to_string(arg, obj=obj)
#         sends = to_string_with_prefix(sends)
#         return f"{name}({arg}{sends})"
#     return ""
