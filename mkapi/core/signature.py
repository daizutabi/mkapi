"""This module provides Signature class that inspects object and creates
signature and types."""
import inspect
from dataclasses import InitVar, dataclass, field
from functools import lru_cache
from typing import Any, Dict, Optional, TypeVar, Union

from mkapi.core import linker


@dataclass
class Signature:
    """Signature class.

    Args:
        obj: Object

    Attributes:
        signature: `inspect.Signature` instance.
        parameters: Parameter dictionary. Key is parameter name
            and value is type string.
        defaults: Default value dictionary. Key is parameter name
            and value is default value.
        attributes: Attribute dictionary for dataclass. Key is attribute name
            and value is type string.
        returns: Returned type string. Used in Returns section.
        yields: Yielded type string. Used in Yields section.
    """

    obj: Any = field(default=None, repr=False)
    signature: Optional[inspect.Signature] = field(default=None, init=False)
    parameters: Dict[str, str] = field(default_factory=dict, init=False)
    defaults: Dict[str, Any] = field(default_factory=dict, init=False)
    attributes: Dict[str, str] = field(default_factory=dict, init=False)
    returns: str = field(default="", init=False)
    yields: str = field(default="", init=False)

    def __post_init__(self):
        if self.obj is None or not callable(self.obj):
            return
        try:
            self.signature = inspect.signature(self.obj)
        except (TypeError, ValueError):
            pass

        for name, parameter in self.signature.parameters.items():
            if name == "self":
                continue
            type = to_string(parameter.annotation)
            default = parameter.default
            if default == inspect.Parameter.empty:
                self.defaults[name] = default
            else:
                self.defaults[name] = f"{default!r}"
                if not type.endswith(", optional"):
                    type += ", optional"
            self.parameters[name] = type

        return_annotation = self.signature.return_annotation
        self.returns = to_string(return_annotation, "returns")
        self.yields = to_string(return_annotation, "yields")

        if hasattr(self.obj, "__dataclass_fields__"):
            values = self.obj.__dataclass_fields__.values()
            attributes = {}
            for field_ in values:
                if field_.type != InitVar:
                    attributes[field_.name] = to_string(field_.type)
            self.attributes = attributes

    def __contains__(self, name):
        return name in self.parameters

    def __getitem__(self, name):
        return getattr(self, name.lower())

    def __str__(self):
        if self.obj is None or not callable(self.obj):
            return ""

        args = []
        for arg in self.parameters:
            if self.defaults[arg] != inspect.Parameter.empty:
                arg += "=" + self.defaults[arg]
            args.append(arg)
        return "(" + ", ".join(args) + ")"


def to_string(annotation, kind: str = "returns") -> str:
    """Returns string expression of annotation.

    If possible, type string includes link.

    Args:
        annotation: Annotation
        kind: 'returns' or 'yields'

    Examples:
        >>> from typing import Iterator, List
        >>> to_string(Iterator[str])
        'iterator of str'
        >>> to_string(Iterator[str], 'yields')
        'str'
        >>> from mkapi.core.node import Node
        >>> to_string(List[Node])
        'list of [Node](!mkapi.core.node.Node)'
    """
    if kind == "yields":
        if hasattr(annotation, "__args__") and annotation.__args__:
            return to_string(annotation.__args__[0])
        else:
            return ""

    if hasattr(annotation, "__forward_arg__"):
        return annotation.__forward_arg__
    if annotation == inspect.Parameter.empty or annotation is None:
        return ""
    name = linker.get_link(annotation)
    if name:
        return name
    if not hasattr(annotation, "__origin__"):
        return str(annotation).replace("typing.", "").lower()
    origin = annotation.__origin__
    if origin is Union:
        return union(annotation)
    if origin is tuple:
        args = [to_string(x) for x in annotation.__args__]
        if args:
            return "(" + ", ".join(args) + ")"
        else:
            return "tuple"
    if origin is dict:
        if type(annotation.__args__[0]) == TypeVar:
            return "dict"
        args = [to_string(x) for x in annotation.__args__]
        if args:
            return "dict(" + ": ".join(args) + ")"
        else:
            return "dict"
    if hasattr(annotation, "__args__") and len(annotation.__args__) <= 1:
        return a_of_b(annotation)
    return ""


def a_of_b(annotation) -> str:
    """Returns A of B style string.

    Args:
        annotation: Annotation

    Examples:
        >>> from typing import List, Iterable, Iterator
        >>> a = List[str]
        >>> a_of_b(a)
        'list of str'
        >>> a = Iterable[int]
        >>> a_of_b(a)
        'iterable of int'
        >>> a = Iterator[float]
        >>> a_of_b(a)
        'iterator of float'
    """
    origin = annotation.__origin__
    if not hasattr(origin, "__name__"):
        return ""
    name = origin.__name__.lower()
    if len(annotation.__args__) == 0:
        return name
    if type(annotation.__args__[0]) == TypeVar:
        return name
    type_ = f"{name} of " + to_string(annotation.__args__[0])
    if type_.endswith(" of T"):
        return name
    return type_


def union(annotation) -> str:
    """Returns a string for union annotation.

    Args:
        annotation: Annotation

    Examples:
        >>> from typing import List, Optional, Tuple, Union
        >>> a = Optional[List[str]]
        >>> union(a)
        'list of str, optional'
        >>> a = Union[str, int]
        >>> union(a)
        'str or int'
        >>> a = Union[str, int, float]
        >>> union(a)
        'str, int, or float'
        >>> a = Union[List[str], Tuple[int, int]]
        >>> union(a)
        'Union(list of str, (int, int))'
    """
    args = annotation.__args__
    if (
        len(args) == 2
        and hasattr(args[1], "__name__")
        and args[1].__name__ == "NoneType"
    ):
        return to_string(args[0]) + ", optional"
    else:
        args = [to_string(x) for x in args]
        if all(" " not in arg for arg in args):
            if len(args) == 2:
                return " or ".join(args)
            else:
                return ", ".join(args[:-1]) + ", or " + args[-1]
        else:
            return "Union(" + ", ".join(to_string(x) for x in args) + ")"


@lru_cache(maxsize=1000)
def get_signature(obj: Any) -> Signature:
    return Signature(obj)
