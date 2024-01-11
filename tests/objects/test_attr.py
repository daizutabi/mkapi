import ast

from mkapi.objects import Attribute, create_members


def _get_attributes(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    return list(create_members(node))


def test_get_attributes():
    src = "class A:\n x=f.g(1,p='2')\n '''docstring'''"
    x = _get_attributes(src)[0]
    assert isinstance(x, Attribute)
    assert x.type is None
    assert isinstance(x.default, ast.Call)
    assert ast.unparse(x.default.func) == "f.g"
    assert x.text
    assert x.text.str == "docstring"
    src = "class A:\n x:X\n y:y\n '''docstring\n a'''\n z=0"
    assigns = _get_attributes(src)
    x, y, z = assigns
    assert isinstance(x, Attribute)
    assert isinstance(y, Attribute)
    assert isinstance(z, Attribute)
    assert not x.text
    assert x.default is None
    assert y.text
    assert y.text.str == "docstring\na"
    assert not z.text
    assert z.default is not None
    assert list(assigns) == [x, y, z]
