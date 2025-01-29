import ast

import pytest
from astdoc.object import Function


def get(src: str) -> Function:
    from astdoc.object import create_function

    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    return create_function(node, "", None)


def test_iter_signature_return():
    from mkapi.parser import _iter_signature

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


def test_iter_signature_return_none():
    from mkapi.parser import _iter_signature

    obj = get("def f(): pass")
    x = list(_iter_signature(obj))
    assert x[0][0] == "("
    assert x[0][1].value == "paren"
    assert x[-1][0] == ")"
    assert x[-1][1].value == "paren"


def sig(src: str) -> str:
    from mkapi.parser import _iter_signature

    obj = get(f"def f({src}): pass")
    return "".join(str(x[0]).replace(" ", "") for x in _iter_signature(obj))


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("x,y,z", "(x,y,z)"),
        ("x,/,y,z", "(x,/,y,z)"),
        ("x,/,*,y,z", "(x,/,\\*,y,z)"),
        ("x,/,y,*,z", "(x,/,y,\\*,z)"),
        ("x,y,z,/", "(x,y,z,/)"),
        ("*,x,y,z", "(\\*,x,y,z)"),
        ("*x,y,**z", "(\\*x,y,\\*\\*z)"),
        ("x,y,/,**z", "(x,y,/,\\*\\*z)"),
    ],
)
def test_iter_signature_kind(src, expected):
    assert sig(src) == expected


def test_get_signature():
    from mkapi.parser import get_signature

    obj = get("def f(x_:str='s',/,*y_,z_=1,**kwargs)->int: pass")
    s = get_signature(obj)
    assert s[0].name == "("
    assert s[0].kind == "paren"
    assert s[1].name == "x\\_"
    assert s[1].kind == "arg"
    assert s[5].name == "'s'"
    v = s[-1].name
    assert isinstance(v, ast.expr)
    assert ast.unparse(v) == "int"
    assert s[-1].kind == "return"


def test_get_signature_attribute_annassign():
    from astdoc.object import Attribute, create_attribute

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


def test_get_signature_attribute_assign():
    from astdoc.object import Attribute, create_attribute

    from mkapi.parser import Signature, get_signature

    src = """x=1"""
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Assign)
    attr = create_attribute("x", node, "", None)
    assert isinstance(attr, Attribute)
    s = get_signature(attr)
    assert s == Signature([])


def test_signature_len():
    from mkapi.parser import Part, PartKind, Signature

    s = Signature([Part("(", PartKind.PAREN)])
    assert len(s) == 1
    s = Signature([Part("(", PartKind.PAREN), Part(")", PartKind.PAREN)])
    assert len(s) == 2


def test_get_signature_skip_self():
    from astdoc.object import get_object

    from mkapi.parser import get_signature

    obj = get_object("astdoc.doc.Item.clone")
    assert obj
    s = get_signature(obj)  # type: ignore
    assert s[0].name == "("  # no self
    assert s[1].name == ")"


def test_get_signature_dont_skip_self_class():
    from astdoc.object import get_object

    from mkapi.parser import get_signature

    obj = get_object("examples.a.ExampleClass")
    assert obj
    s = get_signature(obj)  # type: ignore
    assert s[0].name == "("
    assert s[1].name == "a"
