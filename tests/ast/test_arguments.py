import ast
from inspect import Parameter

from mkapi.ast import get_arguments


def _get_args(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.FunctionDef)
    return get_arguments(node)


def test_get_arguments_1():
    args = _get_args("def f():\n pass")
    assert not args._args  # noqa: SLF001
    args = _get_args("def f(x):\n pass")
    assert args.x.annotation is None
    assert args.x.default is None
    assert args.x.kind is Parameter.POSITIONAL_OR_KEYWORD
    x = _get_args("def f(x=1):\n pass").x
    assert isinstance(x.default, ast.Constant)
    x = _get_args("def f(x:str='s'):\n pass").x
    assert isinstance(x.annotation, ast.Name)
    assert x.annotation.id == "str"
    assert isinstance(x.default, ast.Constant)
    assert x.default.value == "s"
    x = _get_args("def f(x:'X'='s'):\n pass").x
    assert isinstance(x.annotation, ast.Constant)
    assert x.annotation.value == "X"


def test_get_arguments_2():
    x = _get_args("def f(x:tuple[int]=(1,)):\n pass").x
    assert isinstance(x.annotation, ast.Subscript)
    assert isinstance(x.annotation.value, ast.Name)
    assert x.annotation.value.id == "tuple"
    assert isinstance(x.annotation.slice, ast.Name)
    assert x.annotation.slice.id == "int"
    assert isinstance(x.default, ast.Tuple)
    assert isinstance(x.default.elts[0], ast.Constant)
    assert x.default.elts[0].value == 1


def test_get_arguments_3():
    x = _get_args("def f(x:tuple[int,str]=(1,'s')):\n pass").x
    assert isinstance(x.annotation, ast.Subscript)
    assert isinstance(x.annotation.value, ast.Name)
    assert x.annotation.value.id == "tuple"
    assert isinstance(x.annotation.slice, ast.Tuple)
    assert x.annotation.slice.elts[0].id == "int"  # type: ignore
    assert x.annotation.slice.elts[1].id == "str"  # type: ignore
    assert isinstance(x.default, ast.Tuple)
