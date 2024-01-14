import ast
import inspect
import sys
from inspect import Parameter
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.items import (
    Attribute,
    Item,
    Text,
    Type,
    _iter_imports,
    iter_attributes,
    iter_bases,
    iter_merged_items,
    iter_parameters,
    iter_raises,
    iter_returns,
)
from mkapi.objects import create_module
from mkapi.utils import get_module_path


def _get_parameters(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.FunctionDef)
    return list(iter_parameters(node))


def test_create_parameters():
    args = _get_parameters("def f():\n pass")
    assert not args
    args = _get_parameters("def f(x):\n pass")
    assert args[0].type.expr is None
    assert args[0].default is None
    assert args[0].kind is Parameter.POSITIONAL_OR_KEYWORD
    x = _get_parameters("def f(x=1):\n pass")[0]
    assert isinstance(x.default, ast.Constant)
    x = _get_parameters("def f(x:str='s'):\n pass")[0]
    assert x.type.expr
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "str"
    assert isinstance(x.default, ast.Constant)
    assert x.default.value == "s"
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
    assert isinstance(x.default, ast.Tuple)
    assert isinstance(x.default.elts[0], ast.Constant)
    assert x.default.elts[0].value == 1


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
    assert isinstance(x.default, ast.Tuple)


def _get_attributes(source: str):
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    return list(iter_attributes(node))


def test_get_attributes():
    src = "class A:\n x=f.g(1,p='2')\n '''docstring'''"
    x = _get_attributes(src)[0]
    assert isinstance(x, Attribute)
    assert x.type.expr is None
    assert isinstance(x.default, ast.Call)
    assert ast.unparse(x.default.func) == "f.g"
    assert x.text.str == "docstring"
    src = "class A:\n x:X\n y:y\n '''docstring\n a'''\n z=0"
    assigns = _get_attributes(src)
    x, y, z = assigns
    assert isinstance(x, Attribute)
    assert isinstance(y, Attribute)
    assert isinstance(z, Attribute)
    assert not x.text.str
    assert x.default is None
    assert y.text.str == "docstring\na"
    assert not z.text.str
    assert isinstance(z.default, ast.Constant)
    assert z.default.value == 0
    assert list(assigns) == [x, y, z]


@pytest.fixture(scope="module")
def module():
    path = get_module_path("mkdocs.structure.files")
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


def test_iter_import_nodes(module: ast.Module):
    node = next(iter_child_nodes(module))
    assert isinstance(node, ast.ImportFrom)
    assert len(node.names) == 1
    alias = node.names[0]
    assert node.module == "__future__"
    assert alias.name == "annotations"
    assert alias.asname is None


def test_iter_import_nodes_alias():
    src = "import matplotlib.pyplot"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports(node))
    assert len(x) == 2
    assert x[0].fullname == "matplotlib"
    assert x[1].fullname == "matplotlib.pyplot"
    src = "import matplotlib.pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports(node))
    assert len(x) == 1
    assert x[0].fullname == "matplotlib.pyplot"
    assert x[0].name == "plt"
    src = "from matplotlib import pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.ImportFrom)
    x = list(_iter_imports(node))
    assert len(x) == 1
    assert x[0].fullname == "matplotlib.pyplot"
    assert x[0].name == "plt"


def load_module(name):
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    path = get_module_path(name)
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


@pytest.fixture(scope="module")
def google():
    return load_module("examples.styles.example_google")


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
    assert x[0].name == "param1"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "int"
    assert x[1].name == "param2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "str"

    func = get("module_level_function")
    x = list(iter_parameters(func))
    assert x[0].name == "param1"
    assert x[0].type.expr is None
    assert x[0].default is None
    assert x[0].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert x[1].name == "param2"
    assert x[1].type.expr is None
    assert isinstance(x[1].default, ast.Constant)
    assert x[1].default.value is None
    assert x[1].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert x[2].name == "args"
    assert x[2].type.expr is None
    assert x[2].default is None
    assert x[2].kind is Parameter.VAR_POSITIONAL
    assert x[3].name == "kwargs"
    assert x[3].type.expr is None
    assert x[3].default is None
    assert x[3].kind is Parameter.VAR_KEYWORD


def test_create_raises(get):
    func = get("module_level_function")
    x = next(iter_raises(func))
    assert x.name == "ValueError"
    assert x.text.str is None
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "ValueError"


def test_create_returns(get):
    func = get("function_with_pep484_type_annotations")
    x = next(iter_returns(func))
    assert x.name == ""
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "bool"


def test_create_attributes(google, get):
    x = list(iter_attributes(google))
    assert x[0].name == "module_level_variable1"
    assert x[0].type.expr is None
    assert x[0].text.str is None
    assert isinstance(x[0].default, ast.Constant)
    assert x[0].default.value == 12345
    assert x[1].name == "module_level_variable2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "int"
    assert x[1].text.str
    assert x[1].text.str.startswith("Module level")
    assert x[1].text.str.endswith("by a colon.")
    assert isinstance(x[1].default, ast.Constant)
    assert x[1].default.value == 98765
    cls = get("ExamplePEP526Class")
    x = list(iter_attributes(cls))
    assert x[0].name == "attr1"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "str"
    assert x[1].name == "attr2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "int"


def test_create_attributes_from_property(get):
    cls = get("ExampleClass")
    x = list(iter_attributes(cls))
    assert x[0].name == "readonly_property"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "str"
    assert x[0].text.str
    assert x[0].text.str.startswith("Properties should")
    assert x[1].name == "readwrite_property"
    assert isinstance(x[1].type.expr, ast.Subscript)
    assert x[1].text.str
    assert x[1].text.str.startswith("Properties with")


def test_repr():
    e = Item("abc", Type(None), Text(None))
    assert repr(e) == "Item(abc)"
    src = "import matplotlib.pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports(node))
    assert repr(x[0]) == "Import(plt)"


def test_create_bases():
    node = ast.parse("class A(B, C[D]): passs")
    cls = node.body[0]
    assert isinstance(cls, ast.ClassDef)
    bases = iter_bases(cls)
    base = next(bases)
    assert base.name == "B"
    assert isinstance(base.type.expr, ast.Name)
    assert base.type.expr.id == "B"
    base = next(bases)
    assert base.name == "C"
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
    module = create_module(node, "x")
    func = module.get_function("f")
    assert func
    items_ast = func.parameters
    items_doc = func.doc.sections[0].items
    item = next(iter_merged_items(items_ast, items_doc))
    assert item.name == "x"
    assert item.type.expr.id == "int"  # type: ignore
    assert item.default.value == 0  # type: ignore
    assert item.text.str == "parameter."
