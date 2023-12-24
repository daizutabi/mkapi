"""Annotation string."""
import inspect

from mkapi.core import linker


def to_string(
    annotation,  # noqa: ANN001
    kind: str = "returns",
    obj: object = None,
) -> str | type[inspect._empty]:
    """Return string expression of annotation.

    If possible, type string includes link.

    Args:
    ----
        annotation: Annotation
        kind: 'returns' or 'yields'

    Examples:
    --------
        >>> from typing import Callable, Iterator, List
        >>> to_string(Iterator[str])
        'iterator of str'
        >>> to_string(Iterator[str], 'yields')
        'str'
        >>> to_string(Callable)
        'callable'
        >>> to_string(Callable[[int, float], str])
        'callable(int, float: str)'
        >>> from mkapi.core.node import Node
        >>> to_string(List[Node])
        'list of [Node](!mkapi.core.node.Node)'
    """
    empty = inspect.Parameter.empty
    if annotation is empty:
        return empty
    if kind == "yields":
        if hasattr(annotation, "__args__") and annotation.__args__:
            if len(annotation.__args__) == 1:
                return to_string(annotation.__args__[0], obj=obj)
            return to_string(annotation, obj=obj)
        return empty

    if annotation == ...:
        return "..."
    if hasattr(annotation, "__forward_arg__"):
        return resolve_forward_ref(obj, annotation.__forward_arg__)
    if annotation == inspect.Parameter.empty or annotation is None:
        return ""
    name = linker.get_link(annotation)
    if name:
        return name
    if not hasattr(annotation, "__origin__"):
        return str(annotation).replace("typing.", "").lower()
    origin = annotation.__origin__
    if origin is Union:
        return union(annotation, obj=obj)
    if origin is tuple:
        args = [to_string(x, obj=obj) for x in annotation.__args__]
        if args:
            return "(" + ", ".join(args) + ")"
        else:
            return "tuple"
    if origin is dict:
        if type(annotation.__args__[0]) == TypeVar:
            return "dict"
        args = [to_string(x, obj=obj) for x in annotation.__args__]
        if args:
            return "dict(" + ": ".join(args) + ")"
        else:
            return "dict"
    if not hasattr(annotation, "__args__"):
        return ""
    if len(annotation.__args__) == 0:
        return annotation.__origin__.__name__.lower()
    if len(annotation.__args__) == 1:
        return a_of_b(annotation, obj=obj)
    else:
        return to_string_args(annotation, obj=obj)


# def a_of_b(annotation, obj=None) -> str:
#     """Return "A of B" style string.

#     Args:
#     ----
#         annotation: Annotation

#     Examples:
#     --------
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
#     ----
#         annotation: Annotation

#     Examples:
#     --------
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


def to_string_args(annotation, obj=None) -> str:
    """Return a string for callable and generator annotation.

    Args:
    ----
        annotation: Annotation

    Examples:
    --------
        >>> from typing import Callable, List, Tuple, Any
        >>> from typing import Generator, AsyncGenerator
        >>> to_string_args(Callable[[int, List[str]], Tuple[int, int]])
        'callable(int, list of str: (int, int))'
        >>> to_string_args(Callable[[int], Any])
        'callable(int)'
        >>> to_string_args(Callable[[str], None])
        'callable(str)'
        >>> to_string_args(Callable[..., int])
        'callable(...: int)'
        >>> to_string_args(Generator[int, float, str])
        'generator(int, float, str)'
        >>> to_string_args(AsyncGenerator[int, float])
        'asyncgenerator(int, float)'
    """

    def to_string_with_prefix(annotation, prefix: str = ",") -> str:
        s = to_string(annotation, obj=obj)
        if s in ["NoneType", "any"]:
            return ""
        return f"{prefix} {s}"

    args = annotation.__args__
    name = annotation.__origin__.__name__.lower()
    if name == "callable":
        *args, returns = args
        args = ", ".join(to_string(x, obj=obj) for x in args)
        returns = to_string_with_prefix(returns, ":")
        return f"{name}({args}{returns})"
    if name == "generator":
        arg, sends, returns = args
        arg = to_string(arg, obj=obj)
        sends = to_string_with_prefix(sends)
        returns = to_string_with_prefix(returns)
        if not sends and returns:
            sends = ","
        return f"{name}({arg}{sends}{returns})"
    if name == "asyncgenerator":
        arg, sends = args
        arg = to_string(arg, obj=obj)
        sends = to_string_with_prefix(sends)
        return f"{name}({arg}{sends})"
    return ""


def resolve_forward_ref(obj: object, name: str) -> str:
    """Return a resolved name for `typing.ForwardRef`.

    Args:
    ----
        obj: Object
        name: Forward reference name.

    Examples:
    --------
        >>> from mkapi.core.base import Docstring
        >>> resolve_forward_ref(Docstring, 'Docstring')
        '[Docstring](!mkapi.core.base.Docstring)'
        >>> resolve_forward_ref(Docstring, 'invalid_object_name')
        'invalid_object_name'
    """
    if obj is None or not hasattr(obj, "__module__"):
        return name
    module = importlib.import_module(obj.__module__)
    globals = dict(inspect.getmembers(module))
    try:
        type = eval(name, globals)
    except NameError:
        return name
    else:
        return to_string(type)
