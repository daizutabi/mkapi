import inspect


class Signature:
    def __init__(self, obj):
        self.obj = obj
        signature = inspect.signature(obj)
        parameters = signature.parameters
        self.signature = str(signature)
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
        return to_string(annotation.__args__[0], kind)
    return ""
