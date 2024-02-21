import ast

from mkapi.nodes import (
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    get_all_names,
    has_decorator,
    iter_decorator_names,
    resolve,
)
from mkapi.utils import get_module_node


def test_iter_import_asname():
    src = "import matplotlib.pyplot"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports_from_import(node))
    assert len(x) == 2
    for i in [0, 1]:
        assert x[0][i] == "matplotlib"
        assert x[1][i] == "matplotlib.pyplot"
    src = "import matplotlib.pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.Import)
    x = list(_iter_imports_from_import(node))
    assert len(x) == 1
    assert x[0][0] == "plt"
    assert x[0][1] == "matplotlib.pyplot"
    src = "from matplotlib import pyplot as plt"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.ImportFrom)
    x = list(_iter_imports_from_import_from(node, ""))
    assert len(x) == 1
    assert x[0][0] == "plt"
    assert x[0][1] == "matplotlib.pyplot"


def test_get_all_names():
    x = get_all_names("tqdm")
    assert "tqdm" in x
    assert "trange" in x
    x = get_all_names("examples.styles")
    assert "ExampleClassGoogle" in x
    assert "ExampleClassNumPy" in x


def test_resolve():
    assert resolve("tqdm.tqdm") == "tqdm.std.tqdm"
    assert resolve("jinja2.Template") == "jinja2.environment.Template"
    assert resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"
    n = resolve("examples.styles.ExampleClassGoogle")
    assert n == "examples.styles.google.ExampleClass"
    assert resolve("mkapi.objects.ast") == "ast"
    assert resolve("mkapi.objects.ast.ClassDef") == "ast.ClassDef"

    x = resolve("Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"
    x = resolve("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = resolve("mkapi.objects.Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"


def test_iter_decorator_names():
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    assert list(iter_decorator_names(node, "")) == ["a", "b.c", "d"]


def test_get_decorator():
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    assert has_decorator(node, "d", "")
    assert not has_decorator(node, "x", "")
