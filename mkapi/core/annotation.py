import inspect
from typing import Dict, Tuple


def to_string(obj) -> Tuple[Dict[str, str], str, str]:
    signature = inspect.signature(obj)
    parameters = signature.parameters
    parameters_str = {}
    for name in parameters:
        annotation = parameters[name].annotation
        if annotation != inspect.Parameter.empty:
            parameters_str[name] = convert(annotation, "returns")

    annotation = signature.return_annotation
    if annotation != inspect.Parameter.empty:
        return_str = convert(annotation, "returns")
        yield_str = convert(annotation, "yields")
    else:
        return_str = yield_str = ""

    return parameters_str, return_str, yield_str


def convert(annotation, kind: str) -> str:
    print(annotation)
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    if kind == "yields":
        return convert(annotation.__args__[0], kind)
    return ""
