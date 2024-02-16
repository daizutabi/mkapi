import ast
from inspect import Parameter

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.items import (
    Assign,
    create_admonition,
    iter_assigns,
    iter_bases,
    iter_parameters,
    iter_raises,
    iter_returns,
)
from mkapi.utils import get_module_path


def _get_parameters(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.FunctionDef)
    return list(iter_parameters(node))


def test_iter_parameters():
    args = _get_parameters("def f():\n pass")
    assert not args
    args = _get_parameters("def f(x):\n pass")
    assert args[0].type.expr is None
    assert args[0].default.expr is None
    assert args[0].kind is Parameter.POSITIONAL_OR_KEYWORD
    x = _get_parameters("def f(x=1):\n pass")[0]
    assert isinstance(x.default.expr, ast.Constant)
    x = _get_parameters("def f(x:str='s'):\n pass")[0]
    assert x.type.expr
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "str"
    assert isinstance(x.default.expr, ast.Constant)
    assert x.default.expr.value == "s"
    x = _get_parameters("def f(x:'X'='s'):\n pass")[0]
    assert x.type
    assert isinstance(x.type.expr, ast.Constant)
    assert x.type.expr.value == "X"


def test_iter_parameters_tuple():
    x = _get_parameters("def f(x:tuple[int]=(1,)):\n pass")[0]
    assert x.type
    node = x.type.expr
    assert isinstance(node, ast.Subscript)
    assert isinstance(node.value, ast.Name)
    assert node.value.id == "tuple"
    assert isinstance(node.slice, ast.Name)
    assert node.slice.id == "int"
    assert isinstance(x.default.expr, ast.Tuple)
    assert isinstance(x.default.expr.elts[0], ast.Constant)
    assert x.default.expr.elts[0].value == 1


def test_iter_parameters_slice():
    x = _get_parameters("def f(x:tuple[int,str]=(1,'s')):\n pass")[0]
    assert x.type
    node = x.type.expr
    assert isinstance(node, ast.Subscript)
    assert isinstance(node.value, ast.Name)
    assert node.value.id == "tuple"
    assert isinstance(node.slice, ast.Tuple)
    assert node.slice.elts[0].id == "int"  # type: ignore
    assert node.slice.elts[1].id == "str"  # type: ignore
    assert isinstance(x.default.expr, ast.Tuple)


def _get_assigns(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    return list(iter_assigns(node))


def test_iter_assigns():
    src = "class A:\n x=f.g(1,p='2')\n '''docstring'''"
    x = _get_assigns(src)[0]
    assert isinstance(x, Assign)
    assert x.type.expr is None
    assert isinstance(x.default.expr, ast.Call)
    assert ast.unparse(x.default.expr.func) == "f.g"
    assert not x.text.str
    assert x.node.__doc__ == "docstring"
    src = "class A:\n x:X\n y:y\n '''docstring\n a'''\n z=0"
    assigns = _get_assigns(src)
    x, y, z = assigns
    assert isinstance(x, Assign)
    assert isinstance(y, Assign)
    assert isinstance(z, Assign)
    assert not x.text.str
    assert x.default.expr is None
    assert not y.text.str
    assert y.node.__doc__ == "docstring\na"
    assert not z.text.str
    assert isinstance(z.default.expr, ast.Constant)
    assert z.default.expr.value == 0
    assert list(assigns) == [x, y, z]


def load_module(name):
    path = get_module_path(name)
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


@pytest.fixture(scope="module")
def google():
    return load_module("examples.styles.google")


@pytest.fixture(scope="module")
def get(google):
    def get(name, *rest, node=google):
        for child in iter_child_nodes(node):
            if not isinstance(child, ast.FunctionDef | ast.ClassDef):
                continue
            if child.name == name:
                if not rest:
                    return child
                return get(*rest, node=child)
        raise NameError

    return get


def test_create_parameters_google(get):
    func = get("function_with_pep484_type_annotations")
    x = list(iter_parameters(func))
    assert x[0].name.str == "param1"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "int"
    assert x[1].name.str == "param2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "str"

    func = get("module_level_function")
    x = list(iter_parameters(func))
    assert x[0].name.str == "param1"
    assert x[0].type.expr is None
    assert x[0].default.expr is None
    assert x[0].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert x[1].name.str == "param2"
    assert x[1].type.expr is None
    assert isinstance(x[1].default.expr, ast.Constant)
    assert x[1].default.expr.value is None
    assert x[1].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert x[2].name.str == "args"
    assert x[2].type.expr is None
    assert x[2].default.expr is None
    assert x[2].kind is Parameter.VAR_POSITIONAL
    assert x[3].name.str == "kwargs"
    assert x[3].type.expr is None
    assert x[3].default.expr is None
    assert x[3].kind is Parameter.VAR_KEYWORD


def test_create_raises(get):
    func = get("module_level_function")
    x = next(iter_raises(func))
    assert not x.name.str
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "ValueError"


def test_create_returns(get):
    func = get("function_with_pep484_type_annotations")
    x = next(iter_returns(func))
    assert not x.name.str
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "bool"


def test_iter_assigns_google(google, get):
    x = list(iter_assigns(google))
    assert x[0].name.str == "module_level_variable1"
    assert x[0].type.expr is None
    assert not x[0].text.str
    assert isinstance(x[0].default.expr, ast.Constant)
    assert x[0].default.expr.value == 12345
    assert x[1].name.str == "module_level_variable2"
    assert not x[1].type.expr
    assert not x[1].text.str
    assert isinstance(x[1].default.expr, ast.Constant)
    assert x[1].default.expr.value == 98765
    cls = get("ExamplePEP526Class")
    x = list(iter_assigns(cls))
    assert x[0].name.str == "attr1"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "str"
    assert x[1].name.str == "attr2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "int"


def test_create_assigns_from_property(get):
    cls = get("ExampleClass")
    x = list(iter_assigns(cls))
    assert x[0].name.str == "readonly_property"
    assert not x[0].type.expr
    assert not x[0].text.str
    assert x[1].name.str == "readwrite_property"
    assert not x[1].type.expr
    assert not x[1].text.str


def test_create_bases():
    node = ast.parse("class A(B, C[D]): passs")
    cls = node.body[0]
    assert isinstance(cls, ast.ClassDef)
    bases = iter_bases(cls)
    base = next(bases)
    assert not base.name.str
    assert isinstance(base.type.expr, ast.Name)
    assert base.type.expr.id == "B"
    base = next(bases)
    assert not base.name.str
    assert isinstance(base.type.expr, ast.Subscript)
    assert isinstance(base.type.expr.slice, ast.Name)


def test_create_admonition():
    a = create_admonition("See Also", "a: b\nc: d")
    x = '!!! info "See Also"\n    * [__mkapi__.a][]: b\n    * [__mkapi__.c][]: d'
    assert a.text.str == x
