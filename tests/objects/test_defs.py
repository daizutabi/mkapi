import ast

from mkapi.objects import Class, get_module_from_node


def _get(src: str):
    return get_module_from_node(ast.parse(src))


def test_deco():
    module = _get("@f(x,a=1)\nclass A:\n pass")
    cls = module.get("A")
    assert isinstance(cls, Class)
    deco = cls.decorators[0]
    assert isinstance(deco, ast.Call)
