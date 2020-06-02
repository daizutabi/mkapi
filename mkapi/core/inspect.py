import inspect
import re
from typing import Optional


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

    if annotation == inspect.Parameter.empty or annotation is None:
        return ""
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    if hasattr(annotation, "__origin__"):
        if annotation.__origin__ == list:
            type = "list of " + to_string(annotation.__args__[0])
            if type.endswith(" of T"):
                return "list"
            return type
        if annotation.__origin__ == tuple:
            args = [to_string(x) for x in annotation.__args__]
            if args:
                return "(" + ", ".join(args) + ")"
            else:
                return "tuple"
    return str(annotation).replace("typing.", "")
