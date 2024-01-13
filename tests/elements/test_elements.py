import ast
from inspect import Parameter

from mkapi.ast import iter_child_nodes
from mkapi.elements import (
    Element,
    Import,
    Text,
    Type,
    create_attributes,
    create_parameters,
    create_raises,
    create_returns,
    iter_imports,
)


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
    x = list(iter_imports(node))
    assert len(x) == 2
    assert x[0].fullname == "matplotlib"
    assert x[1].fullname == "matplotlib.pyplot"
    src = "import matplotlib.pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(iter_imports(node))
    assert len(x) == 1
    assert x[0].fullname == "matplotlib.pyplot"
    assert x[0].name == "plt"
    src = "from matplotlib import pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.ImportFrom)
    x = list(iter_imports(node))
    assert len(x) == 1
    assert x[0].fullname == "matplotlib.pyplot"
    assert x[0].name == "plt"


def test_create_parameters(get):
    func = get("function_with_pep484_type_annotations")
    x = list(create_parameters(func))
    assert x[0].name == "param1"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "int"
    assert x[1].name == "param2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "str"

    func = get("module_level_function")
    x = list(create_parameters(func))
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
    x = next(create_raises(func))
    assert x.name == "ValueError"
    assert x.text.str is None
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "ValueError"


def test_create_returns(get):
    func = get("function_with_pep484_type_annotations")
    x = next(create_returns(func))
    assert x.name == ""
    assert isinstance(x.type.expr, ast.Name)
    assert x.type.expr.id == "bool"


def test_create_attributes(google, get):
    x = list(create_attributes(google))
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
    x = list(create_attributes(cls))
    assert x[0].name == "attr1"
    assert isinstance(x[0].type.expr, ast.Name)
    assert x[0].type.expr.id == "str"
    assert x[1].name == "attr2"
    assert isinstance(x[1].type.expr, ast.Name)
    assert x[1].type.expr.id == "int"


def test_create_attributes_from_property(get):
    cls = get("ExampleClass")
    x = list(create_attributes(cls))
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
    e = Element("abc", None, Type(None), Text(None))
    assert repr(e) == "Element(abc)"
    src = "import matplotlib.pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(iter_imports(node))
    assert repr(x[0]) == "Import(plt)"
