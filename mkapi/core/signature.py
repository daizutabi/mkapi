import inspect
import re


class Signature:
    def __init__(self, obj):
        self.obj = obj
        try:
            signature = inspect.signature(obj)
        except ValueError:
            self.signature = ""
            self.annotations = "", "", ""
            return

        parameters = signature.parameters
        s = str(signature)
        s = re.sub(r"\[[^:->]*\]", "", s)
        s = re.sub(r":.*?(,|= |\))", r"\1", s)
        s = s.replace("= ", "=")
        s = re.sub(r" ->.*", r"", s)
        s = re.sub(r"(self|cls)(, |)", "", s)
        self.signature = s
        parameters_str = {}
        for name in parameters:
            annotation = parameters[name].annotation
            if annotation != inspect.Parameter.empty:
                parameters_str[name] = to_string(annotation, "returns")

        annotation = signature.return_annotation
        if annotation != inspect.Parameter.empty:
            return_str = to_string(annotation, "returns")
            yield_str = to_string(annotation, "yields")
        else:
            return_str = yield_str = ""
        self.annotations = parameters_str, return_str, yield_str

    def __str__(self):
        return self.signature


def to_string(annotation, kind: str) -> str:
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    if kind == "yields":
        if hasattr(annotation, "__args__") and annotation.__args__:
            return to_string(annotation.__args__[0], kind)
    return ""
