import ast

from mkapi.ast import get_module_from_node


def _get(src: str):
    return get_module_from_node(ast.parse(src))


def test_deco():
    module = _get("@f(x,a=1)\nclass A:\n pass")
    deco = module.get("A").decorators[0]
    assert isinstance(deco, ast.Call)
