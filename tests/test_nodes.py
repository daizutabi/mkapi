import ast

from mkapi.nodes import (
    Import,
    _iter_imports,
    _iter_imports_from,
    get_child_nodes,
    parse,
    resolve_from_module,
)
from mkapi.utils import get_module_node, iter_by_name


def test_iter_import_asname():
    src = "import matplotlib.pyplot"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports(node))
    assert len(x) == 2
    for i in [0, 1]:
        assert x[0][i] == "matplotlib"
        assert x[1][i] == "matplotlib.pyplot"
    src = "import matplotlib.pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports(node))
    assert len(x) == 1
    assert x[0][0] == "plt"
    assert x[0][1] == "matplotlib.pyplot"
    src = "from matplotlib import pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.ImportFrom)
    x = list(_iter_imports_from(node, ""))
    assert len(x) == 1
    assert x[0][0] == "plt"
    assert x[0][1] == "matplotlib.pyplot"


def test_parse_import():
    src = "import a.b.c"
    node = ast.parse(src)
    x = list(parse(node, "m"))
    for k, n in enumerate(["a", "a.b", "a.b.c"]):
        i = x[k][1]
        assert isinstance(i, Import)
        assert i.fullname == n
        assert x[k][0] == n


def test_parse_import_as():
    src = "import a.b.c as d"
    node = ast.parse(src)
    x = parse(node, "m")[0]
    assert x[0] == "d"
    assert isinstance(x[1], Import)
    assert x[1].fullname == "a.b.c"


def test_parse_import_from():
    src = "from x import a, b, c as C"
    node = ast.parse(src)
    x = list(parse(node, "m"))
    for k, n in enumerate("abc"):
        i = x[k][1]
        assert isinstance(i, Import)
        assert i.fullname == f"x.{n}"
        if k == 2:
            assert x[k][0] == "C"
        else:
            assert x[k][0] == n


def test_parse_polars():
    name = "polars"
    node = get_module_node(name)
    assert node
    objs = [x[1] for x in parse(node, name)]
    f = list(iter_by_name(objs, "read_excel"))
    assert len(f) > 1


def test_get_child_nodes():
    name = "altair.vegalite"
    node = get_module_node(name)
    assert node
    x = get_child_nodes(node, name)
    assert len(list(iter_by_name(x, "expr"))) == 1


def test_parse_altair():
    name = "altair"
    node = get_module_node(name)
    assert node
    x = [x for _, x in parse(node, name)]
    assert len(list(iter_by_name(x, "expr"))) == 1


def test_resolve_from_module():
    x = resolve_from_module("Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"
    assert resolve_from_module("ast", "mkapi.objects") == "ast"
    x = resolve_from_module("ast.ClassDef", "mkapi.objects")
    assert x == "ast.ClassDef"

    x = resolve_from_module("jinja2.Template", "mkdocs.plugins")
    assert x == "jinja2.environment.Template"
    x = resolve_from_module("jinja2.XXX", "mkdocs.plugins")
    assert x == "jinja2.XXX"

    for x in ["mkapi", "mkapi.ast", "mkapi.ast.XXX"]:
        y = resolve_from_module(x, "mkapi.nodes")
        assert x == y


def test_resolve_from_module_qualname():
    module = "examples.styles.google"
    name = "ExampleClass"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    name = "ExampleClass.attr1"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    name = "ExampleClass.readonly_property"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    name = "ExampleClass._private"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    module = "examples.styles"
    name = "ExampleClassGoogle"
    x = resolve_from_module(name, module)
    assert x == "examples.styles.google.ExampleClass"
    name = "ExampleClassGoogle.readwrite_property"
    x = resolve_from_module(name, module)
    assert x == "examples.styles.google.ExampleClass.readwrite_property"
