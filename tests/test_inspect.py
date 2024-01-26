import ast

from mkapi.inspect import get_decorator, is_dataclass, iter_signature
from mkapi.objects import Class, Function, create_module
from mkapi.utils import get_by_name, get_module_node


def test_get_decorator():
    name = "mkapi.objects"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    cls = get_by_name(module.classes, "Member")
    assert isinstance(cls, Class)
    assert get_decorator(cls, "dataclasses.dataclass")
    assert is_dataclass(cls)


def get(src: str) -> Function:
    node = ast.parse(src)
    module = create_module("x", node)
    return module.functions[0]


def test_iter_signature_return():
    obj = get("def f(): pass")
    x = list(iter_signature(obj))
    assert x == [("(", "paren"), (")", "paren")]
    obj = get("def f()->bool: pass")
    obj.returns[0].type.html = "bool"
    x = list(iter_signature(obj))
    assert x[:3] == [("(", "paren"), (")", "paren"), ("→", "arrow")]
    assert x[-1] == ("bool", "return")


def sig(src: str) -> str:
    obj = get(f"def f({src}): pass")
    return "".join(x[0] for x in iter_signature(obj))


def test_iter_signature_kind():
    assert sig("x,y,z") == "(x,y,z)"
    assert sig("x,/,y,z") == "(x,/,y,z)"
    assert sig("x,/,*,y,z") == "(x,/,*,y,z)"
    assert sig("x,/,y,*,z") == "(x,/,y,*,z)"
    assert sig("x,y,z,/") == "(x,y,z,/)"
    assert sig("*,x,y,z") == "(*,x,y,z)"
    assert sig("*x,y,**z") == "(*x,y,**z)"
    assert sig("x,y,/,**z") == "(x,y,/,**z)"
