import ast
from inspect import Parameter

from mkapi.objects import iter_parameters


def _get_args(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.FunctionDef)
    return list(iter_parameters(node))


def test_get_parameters_1():
    args = _get_args("def f():\n pass")
    assert not args
    args = _get_args("def f(x):\n pass")
    assert args[0].type is None
    assert args[0].default is None
    assert args[0].kind is Parameter.POSITIONAL_OR_KEYWORD
    x = _get_args("def f(x=1):\n pass")[0]
    assert isinstance(x.default, ast.Constant)
    x = _get_args("def f(x:str='s'):\n pass")[0]
    assert isinstance(x.type, ast.Name)
    assert x.type.id == "str"
    assert isinstance(x.default, ast.Constant)
    assert x.default.value == "s"
    x = _get_args("def f(x:'X'='s'):\n pass")[0]
    assert isinstance(x.type, ast.Constant)
    assert x.type.value == "X"


def test_get_parameters_2():
    x = _get_args("def f(x:tuple[int]=(1,)):\n pass")[0]
    assert isinstance(x.type, ast.Subscript)
    assert isinstance(x.type.value, ast.Name)
    assert x.type.value.id == "tuple"
    assert isinstance(x.type.slice, ast.Name)
    assert x.type.slice.id == "int"
    assert isinstance(x.default, ast.Tuple)
    assert isinstance(x.default.elts[0], ast.Constant)
    assert x.default.elts[0].value == 1


def test_get_parameters_3():
    x = _get_args("def f(x:tuple[int,str]=(1,'s')):\n pass")[0]
    assert isinstance(x.type, ast.Subscript)
    assert isinstance(x.type.value, ast.Name)
    assert x.type.value.id == "tuple"
    assert isinstance(x.type.slice, ast.Tuple)
    assert x.type.slice.elts[0].id == "int"  # type: ignore
    assert x.type.slice.elts[1].id == "str"  # type: ignore
    assert isinstance(x.default, ast.Tuple)
