import ast
import dataclasses

from mkapi.inspect import (
    get_decorator,
    get_signature,
    is_classmethod,
    is_dataclass,
    is_staticmethod,
    iter_decorator_names,
    iter_signature,
)
from mkapi.objects import Class, Function, Member, create_module
from mkapi.utils import get_by_name, get_module_node


def test_iter_decorator_names():
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src)
    module = create_module("a", node)
    f = module.functions[0]
    assert list(iter_decorator_names(f)) == ["a", "b.c", "d"]


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
    assert dataclasses.is_dataclass(Member)
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src)
    module = create_module("a", node)
    f = module.functions[0]
    assert get_decorator(f, "d")
    assert not get_decorator(f, "x")


def test_is_method():
    src = "class A:\n @classmethod\n def f(cls): pass"
    node = ast.parse(src)
    module = create_module("a", node)
    cls = module.classes[0]
    assert isinstance(cls, Class)
    assert is_classmethod(cls.functions[0])
    src = "class A:\n @staticmethod\n def f(cls): pass"
    node = ast.parse(src)
    module = create_module("a", node)
    cls = module.classes[0]
    assert isinstance(cls, Class)
    assert is_staticmethod(cls.functions[0])


# TODO
# def test_iter_dataclass_parameters():
#     obj = get_object("mkapi.objects.Class")
#     assert isinstance(obj, Class)
#     print(obj.attributes)
#     print(list(iter_dataclass_parameters(obj)))


def get(src: str) -> Function:
    node = ast.parse(src)
    module = create_module("x", node)
    return module.functions[0]


def test_iter_signature_return():
    obj = get("def f(): pass")
    x = list(iter_signature(obj))
    assert x == [("(", "paren"), (")", "paren")]
    obj = get("def f()->bool: pass")
    obj.returns[0].type.markdown = "bool"
    x = list(iter_signature(obj))
    assert x[:3] == [("(", "paren"), (")", "paren"), (" → ", "arrow")]
    assert x[-1] == ("bool", "return")


def sig(src: str) -> str:
    obj = get(f"def f({src}): pass")
    return "".join(x[0].replace(" ", "") for x in iter_signature(obj))


def test_iter_signature_kind():
    assert sig("x,y,z") == "(x,y,z)"
    assert sig("x,/,y,z") == "(x,/,y,z)"
    assert sig("x,/,*,y,z") == "(x,/,\\*,y,z)"
    assert sig("x,/,y,*,z") == "(x,/,y,\\*,z)"
    assert sig("x,y,z,/") == "(x,y,z,/)"
    assert sig("*,x,y,z") == "(\\*,x,y,z)"
    assert sig("*x,y,**z") == "(\\*x,y,\\*\\*z)"
    assert sig("x,y,/,**z") == "(x,y,/,\\*\\*z)"


def test_get_signature():
    obj = get("def f(x_:str='s',/,*y_,z_=1,**kwargs)->int: pass")
    for x in obj.parameters:
        print(x.name.str, x.name.markdown)
    s = list(get_signature(obj))
    assert s[0].kind == "paren"
    assert s[0].markdown == "("
    assert s[1].kind == "arg"
    assert s[1].markdown == "x\\_"
