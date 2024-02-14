import ast
import inspect
import sys
from inspect import Parameter
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.items import (
    Assign,
    Item,
    Text,
    Type,
    create_admonition,
    iter_assigns,
    iter_bases,
    iter_merged_items,
    iter_parameters,
    iter_raises,
    iter_returns,
)
from mkapi.objects import create_module
from mkapi.utils import get_by_name, get_module_path


def _get_parameters(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.FunctionDef)
    return list(iter_parameters(node))


def test_create_parameters():
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


def test_create_parameters_tuple():
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


def test_create_parameters_slice():
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


def _get_attributes(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    return list(iter_assigns(node))


def test_get_attributes():
    src = "class A:\n x=f.g(1,p='2')\n '''docstring'''"
    x = _get_attributes(src)[0]
    assert isinstance(x, Assign)
    assert x.type.expr is None
    assert isinstance(x.default.expr, ast.Call)
    assert ast.unparse(x.default.expr.func) == "f.g"
    assert x.text.str == "docstring"
    src = "class A:\n x:X\n y:y\n '''docstring\n a'''\n z=0"
    assigns = _get_attributes(src)
    x, y, z = assigns
    assert isinstance(x, Assign)
    assert isinstance(y, Assign)
    assert isinstance(z, Assign)
    assert not x.text.str
    assert x.default.expr is None
    assert y.text.str == "docstring\na"
    assert not z.text.str
    assert isinstance(z.default.expr, ast.Constant)
    assert z.default.expr.value == 0
    assert list(assigns) == [x, y, z]


def load_module(name):
    path = str(Path(__file__).parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
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
    assert x.name.str == "ValueError"
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "ValueError"


def test_create_returns(get):
    func = get("function_with_pep484_type_annotations")
    x = next(iter_returns(func))
    assert x.name.str == ""
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "bool"


def test_create_assings(google, get):
    x = list(iter_assigns(google))
    assert x[0].name.str == "module_level_variable1"
    assert x[0].type.expr is None
    assert x[0].text.str is None
    assert isinstance(x[0].default.expr, ast.Constant)
    assert x[0].default.expr.value == 12345
    assert x[1].name.str == "module_level_variable2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "int"
    assert x[1].text.str
    assert x[1].text.str.startswith("Module level")
    assert x[1].text.str.endswith("by a colon.")
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
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "str"
    assert x[0].text.str
    assert x[0].text.str.startswith("Properties should")
    assert x[1].name.str == "readwrite_property"
    assert isinstance(x[1].type.expr, ast.Subscript)
    assert x[1].text.str
    assert x[1].text.str.startswith("Properties with")


def test_create_bases():
    node = ast.parse("class A(B, C[D]): passs")
    cls = node.body[0]
    assert isinstance(cls, ast.ClassDef)
    bases = iter_bases(cls)
    base = next(bases)
    assert base.name.str == "B"
    assert isinstance(base.type.expr, ast.Name)
    assert base.type.expr.id == "B"
    base = next(bases)
    assert base.name.str == "C"
    assert isinstance(base.type.expr, ast.Subscript)
    assert isinstance(base.type.expr.slice, ast.Name)


def test_iter_merged_items():
    """'''test'''
    def f(x: int=0):
        '''function.

        Args:
            x: parameter.'''
    """
    src = inspect.getdoc(test_iter_merged_items)
    assert src
    node = ast.parse(src)
    module = create_module("x", node)
    func = get_by_name(module.functions, "f")
    assert func
    items_ast = func.parameters
    items_doc = func.doc.sections[0].items
    item = next(iter_merged_items(items_ast, items_doc))
    assert item.name == "x"
    assert item.type.expr.id == "int"  # type: ignore
    assert item.default.expr.value == 0  # type: ignore
    assert item.text.str == "parameter."


def test_iter_merged_items_():
    a = [
        Item("a", Type(), Text("item a")),
        Item("b", Type(ast.Constant("int")), Text("item b")),
    ]
    b = [
        Item("a", Type(ast.Constant("str")), Text("item A")),
        Item("c", Type(ast.Constant("list")), Text("item c")),
    ]
    c = list(iter_merged_items(a, b))
    assert c[0].name == "a"
    assert c[0].type.expr.value == "str"  # type: ignore
    assert c[0].text.str == "item a"
    assert c[1].name == "b"
    assert c[1].type.expr.value == "int"  # type: ignore
    assert c[2].name == "c"
    assert c[2].type.expr.value == "list"  # type: ignore


def test_create_admonition():
    a = create_admonition("See Also", "a: b\nc: d")
    x = '!!! info "See Also"\n    * [__mkapi__.a][]: b\n    * [__mkapi__.c][]: d'
    assert a.text.str == x
