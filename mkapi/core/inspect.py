import inspect
import re
from typing import ForwardRef, Optional, Union  # type:ignore


class Signature:
    def __init__(self, obj):
        try:
            self.signature = inspect.signature(obj)
        except (TypeError, ValueError):
            self.signature = None

    def __str__(self):
        if self.signature is None:
            return ""
        s = str(self.signature)
        s = re.sub(r"\[[^:->]*\]", "", s)
        s = re.sub(r":.*?(,|= |\))", r"\1", s)
        s = s.replace("= ", "=")
        s = re.sub(r" ->.*", r"", s)
        s = re.sub(r"(self|cls)(, |)", "", s)
        return s


def get_signature(obj) -> Optional[Signature]:
    if not callable(obj):
        return None
    signature = Signature(obj)
    if signature.signature:
        return signature
    return None


class Annotation:
    def __init__(self, obj):
        signature = inspect.signature(obj)
        self.parameters = signature.parameters
        self.defaults = {}
        for name, param in self.parameters.items():
            if param.default == inspect.Parameter.empty:
                self.defaults[name] = param.default
            else:
                self.defaults[name] = str(param.default)
        self.return_annotation = signature.return_annotation
        if hasattr(obj, "__dataclass_fields__"):
            values = obj.__dataclass_fields__.values()
            self.attributes = {f.name: to_string(f.type) for f in values}
        else:
            self.attributes = None

    def __contains__(self, name):
        return name in self.parameters

    def __getitem__(self, name):
        type = to_string(self.parameters[name].annotation)
        if self.defaults[name] != inspect.Parameter.empty:
            if not type.endswith(", optional"):
                type += ", optional"
        return type

    @property
    def returns(self):
        return to_string(self.return_annotation)

    @property
    def yields(self):
        return to_string(self.return_annotation, "yields")


def to_string(annotation, kind: str = "") -> str:
    if kind == "yields":
        if hasattr(annotation, "__args__") and annotation.__args__:
            return to_string(annotation.__args__[0])
        else:
            return ""

    if isinstance(annotation, ForwardRef):
        return annotation.__forward_arg__
    if annotation == inspect.Parameter.empty or annotation is None:
        return ""
    if hasattr(annotation, "__name__"):
        name = annotation.__name__
        if not hasattr(annotation, '__module__'):
            return name
        module = annotation.__module__
        if module == 'builtins':
            return name
        return f"[{name}]({module}.{name})"
    if not hasattr(annotation, "__origin__"):
        return str(annotation).replace("typing.", "")
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
        args = [to_string(x) for x in annotation.__args__]
        if args:
            return "dict(" + ": ".join(args) + ")"
        else:
            return "dict"
    if hasattr(annotation, "__args__") and len(annotation.__args__) <= 1:
        return a_of_b(annotation)
    return ""


def a_of_b(annotation) -> str:
    origin = annotation.__origin__
    if not hasattr(origin, "__name__"):
        return ""
    name = origin.__name__.lower()
    type = f"{name} of " + to_string(annotation.__args__[0])
    if type.endswith(" of T"):
        return name
    return type


def union(annotation) -> str:
    """Returns a string for union annotation.

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
