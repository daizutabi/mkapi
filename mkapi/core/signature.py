"""This module provides Signature class that inspects object and creates
signature and types."""
import importlib
import inspect
from dataclasses import InitVar, dataclass, field, is_dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, TypeVar, Union

from mkapi.core import linker, preprocess
from mkapi.core.attribute import get_attributes
from mkapi.core.base import Inline, Item, Section, Type


@dataclass
class Signature:
    """Signature class.

    Args:
        obj: Object

    Attributes:
        signature: `inspect.Signature` instance.
        parameters: Parameters section.
        defaults: Default value dictionary. Key is parameter name and
            value is default value.
        attributes: Attributes section.
        returns: Returned type string. Used in Returns section.
        yields: Yielded type string. Used in Yields section.
    """

    obj: Any = field(default=None, repr=False)
    signature: Optional[inspect.Signature] = field(default=None, init=False)
    parameters: Section = field(default_factory=Section, init=False)
    defaults: Dict[str, Any] = field(default_factory=dict, init=False)
    attributes: Section = field(default_factory=Section, init=False)
    returns: str = field(default="", init=False)
    yields: str = field(default="", init=False)

    def __post_init__(self):
        if self.obj is None:
            return
        try:
            self.signature = inspect.signature(self.obj)
        except (TypeError, ValueError):
            self.set_attributes()
            return

        items = []
        for name, parameter in self.signature.parameters.items():
            if name == "self":
                continue
            elif parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                name = "*" + name
            elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
                name = "**" + name
            if isinstance(parameter.annotation, str):
                type = resolve_forward_ref(self.obj, parameter.annotation)
            else:
                type = to_string(parameter.annotation, obj=self.obj)
            default = parameter.default
            if default == inspect.Parameter.empty:
                self.defaults[name] = default
            else:
                self.defaults[name] = f"{default!r}"
                if not type:
                    type = "optional"
                elif not type.endswith(", optional"):
                    type += ", optional"
            items.append(Item(name, Type(type)))
        self.parameters = Section("Parameters", items=items)
        self.set_attributes()
        return_annotation = self.signature.return_annotation

        if isinstance(return_annotation, str):
            self.returns = resolve_forward_ref(self.obj, return_annotation)
        else:
            self.returns = to_string(return_annotation, "returns", obj=self.obj)
            self.yields = to_string(return_annotation, "yields", obj=self.obj)

    def __contains__(self, name):
        return name in self.parameters

    def __getitem__(self, name):
        return getattr(self, name.lower())

    def __str__(self):
        args = self.arguments
        if args is None:
            return ""
        else:
            return "(" + ", ".join(args) + ")"

    @property
    def arguments(self) -> Optional[List[str]]:
        """Returns arguments list."""
        if self.obj is None or not callable(self.obj):
            return None

        args = []
        for item in self.parameters.items:
            arg = item.name
            if self.defaults[arg] != inspect.Parameter.empty:
                arg += "=" + self.defaults[arg]
            args.append(arg)
        return args

    def set_attributes(self):
        """
        Examples:
            >>> from mkapi.core.base import Base
            >>> s = Signature(Base)
            >>> s.parameters['name'].to_tuple()
            ('name', 'str, optional', 'Name of self.')
            >>> s.attributes['html'].to_tuple()
            ('html', 'str', 'HTML output after conversion.')
        """
        items = []
        for name, (type, description) in get_attributes(self.obj).items():
            if isinstance(type, str) and type:
                type = resolve_forward_ref(self.obj, type)
            else:
                type = to_string(type, obj=self.obj) if type else ""
            if not type:
                type, description = preprocess.split_type(description)

            item = Item(name, Type(type), Inline(description))
            if is_dataclass(self.obj):
                if name in self.parameters:
                    self.parameters[name].set_description(item.description)
                if self.obj.__dataclass_fields__[name].type != InitVar:
                    items.append(item)
            else:
                items.append(item)
        self.attributes = Section("Attributes", items=items)

    def split(self, sep=","):
        return str(self).split(sep)


def to_string(annotation, kind: str = "returns", obj=None) -> str:
    """Returns string expression of annotation.

    If possible, type string includes link.

    Args:
        annotation: Annotation
        kind: 'returns' or 'yields'

    Examples:
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
    if kind == "yields":
        if hasattr(annotation, "__args__") and annotation.__args__:
            if len(annotation.__args__) == 1:
                return to_string(annotation.__args__[0], obj=obj)
            else:
                return to_string(annotation, obj=obj)
        else:
            return ""

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


def a_of_b(annotation, obj=None) -> str:
    """Returns A of B style string.

    Args:
        annotation: Annotation

    Examples:
        >>> from typing import List, Iterable, Iterator
        >>> a_of_b(List[str])
        'list of str'
        >>> a_of_b(List[List[str]])
        'list of list of str'
        >>> a_of_b(Iterable[int])
        'iterable of int'
        >>> a_of_b(Iterator[float])
        'iterator of float'
    """
    origin = annotation.__origin__
    if not hasattr(origin, "__name__"):
        return ""
    name = origin.__name__.lower()
    if type(annotation.__args__[0]) == TypeVar:
        return name
    type_ = f"{name} of " + to_string(annotation.__args__[0], obj=obj)
    if type_.endswith(" of T"):
        return name
    return type_


def union(annotation, obj=None) -> str:
    """Returns a string for union annotation.

    Args:
        annotation: Annotation

    Examples:
        >>> from typing import List, Optional, Tuple, Union
        >>> union(Optional[List[str]])
        'list of str, optional'
        >>> union(Union[str, int])
        'str or int'
        >>> union(Union[str, int, float])
        'str, int, or float'
        >>> union(Union[List[str], Tuple[int, int]])
        'Union(list of str, (int, int))'
    """
    args = annotation.__args__
    if (
        len(args) == 2
        and hasattr(args[1], "__name__")
        and args[1].__name__ == "NoneType"
    ):
        return to_string(args[0], obj=obj) + ", optional"
    else:
        args = [to_string(x, obj=obj) for x in args]
        if all(" " not in arg for arg in args):
            if len(args) == 2:
                return " or ".join(args)
            else:
                return ", ".join(args[:-1]) + ", or " + args[-1]
        else:
            return "Union(" + ", ".join(to_string(x, obj=obj) for x in args) + ")"


def to_string_args(annotation, obj=None) -> str:
    """Returns a string for callable and generator annotation.

    Args:
        annotation: Annotation

    Examples:
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

    def to_string_with_prefix(annotation, prefix=","):
        s = to_string(annotation, obj=obj)
        if s in ["NoneType", "any"]:
            return ""
        else:
            return " ".join([prefix, s])

    args = annotation.__args__
    name = annotation.__origin__.__name__.lower()
    if name == "callable":
        *args, returns = args
        args = ", ".join(to_string(x, obj=obj) for x in args)
        returns = to_string_with_prefix(returns, ":")
        return f"{name}({args}{returns})"
    elif name == "generator":
        arg, sends, returns = args
        arg = to_string(arg, obj=obj)
        sends = to_string_with_prefix(sends)
        returns = to_string_with_prefix(returns)
        if not sends and returns:
            sends = ","
        return f"{name}({arg}{sends}{returns})"
    elif name == "asyncgenerator":
        arg, sends = args
        arg = to_string(arg, obj=obj)
        sends = to_string_with_prefix(sends)
        return f"{name}({arg}{sends})"
    else:
        return ""


def resolve_forward_ref(obj: Any, name: str) -> str:
    """Returns a resolved name for `typing.ForwardRef`.

    Args:
        obj: Object
        name: Forward reference name.

    Examples:
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


@lru_cache(maxsize=1000)
def get_signature(obj: Any) -> Signature:
    return Signature(obj)
