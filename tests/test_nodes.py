import ast

from mkapi.nodes import (
    Object,
    _get_fullname,
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    _parse,
    _resolve,
    get_all_names,
    has_decorator,
    iter_decorator_names,
    resolve,
    resolve_from_module,
    resolve_module_name,
)


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


def test_get_fullname():
    src = "from collections.abc import Iterator"
    node = ast.parse(src)
    name, obj = _parse(node, "")[0]
    assert name == "Iterator"
    assert isinstance(obj, Object)
    assert obj.module == "_collections_abc"
    assert _get_fullname(obj) == "collections.abc.Iterator"


def test_resolve_module_name():
    name = "examples.styles.google"
    x = resolve_module_name(name)
    assert x == ("examples.styles.google", None)
    name = "examples.styles.google.ExampleClass"
    x = resolve_module_name(name)
    assert x == ("examples.styles.google", "ExampleClass")
    name = "examples.styles.ExampleClassGoogle"
    x = resolve_module_name(name)
    assert x == ("examples.styles.google", "ExampleClass")


def test_resolve():
    assert resolve("tqdm.tqdm") == "tqdm.std.tqdm"
    assert resolve("jinja2.Template") == "jinja2.environment.Template"
    assert resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"
    n = resolve("examples.styles.ExampleClassGoogle")
    assert n == "examples.styles.google.ExampleClass"
    assert resolve("mkapi.objects.ast") == "ast"
    assert resolve("mkapi.objects.ast.ClassDef") == "ast.ClassDef"


def test_resolve_from_module():
    x = resolve_from_module("Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"
    x = resolve_from_module("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = resolve_from_module("mkapi.objects.Class", "mkapi.objects")
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
