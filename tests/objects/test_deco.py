import ast

from mkapi.objects import Class, get_module_from_source


def test_deco():
    module = get_module_from_source("@f(x,a=1)\nclass A:\n pass")
    cls = module.get("A")
    assert isinstance(cls, Class)
    deco = cls.decorators[0]
    assert isinstance(deco, ast.Call)
