import ast

from mkapi.objects import (
    Class,
    Function,
    Module,
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    _resolve,
    create_module,
    get_fullname,
    get_member,
    get_members,
    get_members_all,
    get_source,
    has_decorator,
    is_dataclass,
    iter_decorator_names,
    resolve,
)
from mkapi.utils import get_by_name


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


def test_get_members():
    x = get_members("mkdocs.plugins")
    assert "jinja2.environment" in x
    assert "Page" in x


def test_get_members_all():
    x = get_members_all("tqdm")
    assert x["tqdm"].module == "tqdm.std"  # type:ignore
    assert x["main"].module == "tqdm.cli"  # type:ignore
    assert x["TqdmTypeError"].module == "tqdm.std"  # type: ignore
    x = get_members_all("examples.styles")
    assert x["ExampleClassGoogle"].module == "examples.styles.google"  # type:ignore
    assert x["ExampleClassNumPy"].module == "examples.styles.numpy"  # type:ignore


def test_get_member():
    x = get_member("ast", "mkapi.objects")
    assert isinstance(x, Module)
    assert not get_member("ast.ClassDef", "mkapi.objects")  # built-in
    x = get_member("ast.unparse", "mkapi.objects")
    assert isinstance(x, Function)
    x = get_member("ast.Index", "mkapi.objects")
    assert isinstance(x, Class)


def test_resolve():
    c = _resolve("tqdm.tqdm")
    assert isinstance(c, Class)
    assert c.module == "tqdm.std"
    assert resolve("tqdm.tqdm") == "tqdm.std.tqdm"
    c = _resolve("jinja2.Template")
    assert isinstance(c, Class)
    assert c.module == "jinja2.environment"
    assert resolve("jinja2.Template") == "jinja2.environment.Template"
    c = _resolve("mkdocs.config.Config")
    assert isinstance(c, Class)
    assert c.module == "mkdocs.config.base"
    assert resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"
    c = _resolve("examples.styles.ExampleClassGoogle")
    assert isinstance(c, Class)
    assert c.module == "examples.styles.google"
    n = resolve("examples.styles.ExampleClassGoogle")
    assert n == "examples.styles.google.ExampleClass"
    assert resolve("mkapi.objects.ast") == "ast"
    assert resolve("mkapi.objects.ast.ClassDef") == "ast.ClassDef"


def test_get_fullname():
    x = get_fullname("Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"
    x = get_fullname("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = get_fullname("mkapi.objects.Class", "mkapi.objects")
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


def test_is_dataclass():
    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Node")
    assert isinstance(cls, Class)
    assert is_dataclass(cls.node, "mkapi.objects")


def test_class_parameters():
    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    assert len(cls.parameters) == 3
    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    assert get_by_name(cls.parameters, "name")
    assert get_by_name(cls.parameters, "dict")


def test_get_source():
    module = create_module("mkapi.objects")
    assert module
    s = get_source(module)
    assert s
    assert "def load_module(" in s
    func = module.get("create_module")
    assert isinstance(func, Function)
    assert func
    s = get_source(func)
    assert s
    assert s.startswith("def create_module")
