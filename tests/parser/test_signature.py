import ast

from mkapi.object import Function


def get(src: str) -> Function:
    from mkapi.object import create_function

    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    return create_function(node, "", None)


def test_iter_signature_return():
    from mkapi.parser import _iter_signature

    obj = get("def f(): pass")
    x = list(_iter_signature(obj))
    assert x[0][0] == "("
    assert x[0][1].value == "paren"
    assert x[-1][0] == ")"
    assert x[-1][1].value == "paren"
    obj = get("def f()->bool: pass")
    x = list(_iter_signature(obj))
    assert x[0][0] == "("
    assert x[0][1].value == "paren"
    assert x[1][0] == ")"
    assert x[1][1].value == "paren"
    assert x[2][0] == " → "
    assert x[2][1].value == "arrow"
    r = x[-1][0]
    assert isinstance(r, ast.expr)
    assert ast.unparse(r) == "bool"
    assert x[-1][1].value == "return"


def sig(src: str) -> str:
    from mkapi.parser import _iter_signature

    obj = get(f"def f({src}): pass")
    return "".join(str(x[0]).replace(" ", "") for x in _iter_signature(obj))


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
    from mkapi.parser import get_signature

    obj = get("def f(x_:str='s',/,*y_,z_=1,**kwargs)->int: pass")
    s = get_signature(obj)
    assert s[0].name == "("
    assert s[0].kind == "paren"
    assert s[1].name == "x\\_"
    assert s[1].kind == "arg"
    v = s[-1].name
    assert isinstance(v, ast.expr)
    assert ast.unparse(v) == "int"
    assert s[-1].kind == "return"


def test_get_signature_attribute():
    from mkapi.object import Attribute, create_attribute
    from mkapi.parser import get_signature

    src = """x:int"""
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.AnnAssign)
    attr = create_attribute("x", node, "", None)
    assert isinstance(attr, Attribute)
    s = get_signature(attr)
    assert s[0].name == ": "
    assert s[0].kind == "colon"
    assert isinstance(s[-1].name, ast.expr)
    assert ast.unparse(s[-1].name) == "int"
    assert s[-1].kind == "return"
