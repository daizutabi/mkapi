import ast
import dataclasses

from mkapi.inspect import (
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    _iter_members,
    get_decorator,
    get_fullname,
    get_member,
    get_members,
    get_members_all,
    is_classmethod,
    is_dataclass,
    is_staticmethod,
    iter_decorator_names,
    resolve,
)
from mkapi.objects import Class, Member, _create_module
from mkapi.utils import get_by_name, get_module_node


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


def test_resolve():
    assert resolve("tqdm.tqdm") == "tqdm.std.tqdm"
    assert resolve("logging.Template") == "string.Template"
    assert resolve("halo.Halo") == "halo.halo.Halo"
    assert resolve("jinja2.Template") == "jinja2.environment.Template"
    assert resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"
    x = resolve("examples.styles.ExampleClassGoogle")
    assert x == "examples.styles.google.ExampleClass"
    x = resolve("mkapi.inspect.Iterator")
    assert x == "collections.abc.Iterator"


def test_get_member():
    x = get_member("MkDocsPage", "mkapi.plugins")
    assert x
    assert isinstance(x.node, ast.ClassDef)
    x = get_member("config_options.Type", "mkapi.plugins")
    assert x
    assert isinstance(x.node, ast.ClassDef)
    x = get_member("tqdm", "mkapi.plugins")
    assert x
    assert isinstance(x.node, ast.ClassDef)
    x = get_member("renderers", "mkapi.plugins")
    assert x
    assert isinstance(x.node, ast.Module)


def test_get_fullname():
    x = get_fullname("MkDocsPage", "mkapi.plugins")
    assert x == "mkdocs.structure.pages.Page"
    x = get_fullname("config_options.Type", "mkapi.plugins")
    assert x == "mkdocs.config.config_options.Type"
    x = get_fullname("jinja2.Template", "mkdocs.plugins")
    assert x == "jinja2.environment.Template"
    x = get_fullname("Object", "mkapi.objects")
    assert x == "mkapi.objects.Object"
    x = get_fullname("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = get_fullname("mkapi.objects.Object", "mkapi.objects")
    assert x == "mkapi.objects.Object"
    x = get_fullname("Iterator", "mkapi.inspect")
    assert x == "collections.abc.Iterator"


def test_iter_decorator_names():
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src)
    module = _create_module("a", node)
    f = module.functions[0]
    assert list(iter_decorator_names(f)) == ["a", "b.c", "d"]


def test_get_decorator():
    name = "mkapi.objects"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    assert module
    cls = get_by_name(module.classes, "Member")
    assert isinstance(cls, Class)
    assert get_decorator(cls, "dataclasses.dataclass")
    assert is_dataclass(cls)
    assert dataclasses.is_dataclass(Member)
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src)
    module = _create_module("a", node)
    f = module.functions[0]
    assert get_decorator(f, "d")
    assert not get_decorator(f, "x")


def test_is_method():
    src = "class A:\n @classmethod\n def f(cls): pass"
    node = ast.parse(src)
    module = _create_module("a", node)
    cls = module.classes[0]
    assert isinstance(cls, Class)
    assert is_classmethod(cls.functions[0])
    src = "class A:\n @staticmethod\n def f(cls): pass"
    node = ast.parse(src)
    module = _create_module("a", node)
    cls = module.classes[0]
    assert isinstance(cls, Class)
    assert is_staticmethod(cls.functions[0])


def test_get_members_all():
    x = get_members_all("tqdm")
    assert x["tqdm"].module == "tqdm.std"  # type:ignore
    assert x["main"].module == "tqdm.cli"  # type:ignore
    assert x["TqdmTypeError"].module == "tqdm.std"  # type: ignore


def test_get_all():
    x = get_members_all("examples.styles")
    assert "ExampleClassGoogle" in x
    assert "ExampleClassNumPy" in x
