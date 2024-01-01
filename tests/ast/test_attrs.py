import ast

from mkapi.ast.node import get_attributes


def _get_attributes(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    return get_attributes(node)


def test_get_attributes():
    src = "class A:\n x=f.g(1,p='2')\n '''docstring'''"
    x = _get_attributes(src).x
    assert x.annotation is None
    assert isinstance(x.value, ast.Call)
    assert ast.unparse(x.value.func) == "f.g"
    assert x.docstring == "docstring"
    src = "class A:\n x:X\n y:y\n '''docstring\n a'''\n z=0"
    assigns = _get_attributes(src)
    x, y, z = assigns.items
    assert x.docstring is None
    assert x.value is None
    assert y.docstring == "docstring\na"
    assert z.docstring is None
    assert z.value is not None
    assert list(assigns) == [x, y, z]
