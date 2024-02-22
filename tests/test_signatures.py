import ast

from mkapi.objects import Function, _create_module
from mkapi.parsers import set_markdown
from mkapi.signatures import get_signature, iter_signature


def get(src: str) -> Function:
    node = ast.parse(src)
    module = _create_module("x", node)
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
    set_markdown(obj)
    s = list(get_signature(obj))
    assert s[0].kind == "paren"
    assert s[0].markdown == "("
    assert s[1].kind == "arg"
    assert s[1].markdown == "x\\_"
    assert s[-1].markdown == "int"


def test_get_signature_attribute():
    src = """x:int"""
    node = ast.parse(src)
    module = _create_module("x", node)
    attr = module.attributes[0]
    set_markdown(attr)
    s = list(get_signature(attr))
    assert s[0].kind == "colon"
    assert s[0].markdown == ": "
    assert s[1].kind == "return"
    assert s[1].markdown == "int"
