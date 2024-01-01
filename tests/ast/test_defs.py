import ast


def _get_def(src: str):
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.ClassDef | ast.FunctionDef)
    return node


def test_deco():
    node = _get_def("@f(x,a=1)\nclass A:\n pass")
    assert isinstance(node, ast.ClassDef)
    print(node.decorator_list)
    node.type_params
    assert 0
