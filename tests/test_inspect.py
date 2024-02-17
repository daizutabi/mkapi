import ast
import dataclasses

from mkapi.inspect import (
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    get_decorator,
    get_members,
    is_classmethod,
    is_dataclass,
    is_staticmethod,
    iter_decorator_names,
    resolve,
)
from mkapi.objects import Class, Member, _create_module
from mkapi.utils import get_by_name, get_module_node, get_module_node_source


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
    assert resolve("tqdm.tqdm").fullname == "tqdm.std.tqdm"
    # assert resolve("logging.Template") == "string.Template"
    # assert resolve("halo.Halo") == "halo.halo.Halo"
    # assert resolve("jinja2.Template") == "jinja2.environment.Template"
    # assert resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"


# def test_get_members():
#     module = "polars"
#     m = get_members(module)
#     for x in m.items():
#         print(x)
#     x = get_module_node_source(module)
#     # print(x[1])
#     assert 0


# def test_iter_decorator_names():
#     src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
#     node = ast.parse(src)
#     module = _create_module("a", node)
#     f = module.functions[0]
#     assert list(iter_decorator_names(f)) == ["a", "b.c", "d"]


# def test_get_decorator():
#     name = "mkapi.objects"
#     node = get_module_node(name)
#     assert node
#     module = _create_module(name, node)
#     assert module
#     cls = get_by_name(module.classes, "Member")
#     assert isinstance(cls, Class)
#     assert get_decorator(cls, "dataclasses.dataclass")
#     assert is_dataclass(cls)
#     assert dataclasses.is_dataclass(Member)
#     src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
#     node = ast.parse(src)
#     module = _create_module("a", node)
#     f = module.functions[0]
#     assert get_decorator(f, "d")
#     assert not get_decorator(f, "x")


# def test_is_method():
#     src = "class A:\n @classmethod\n def f(cls): pass"
#     node = ast.parse(src)
#     module = _create_module("a", node)
#     cls = module.classes[0]
#     assert isinstance(cls, Class)
#     assert is_classmethod(cls.functions[0])
#     src = "class A:\n @staticmethod\n def f(cls): pass"
#     node = ast.parse(src)
#     module = _create_module("a", node)
#     cls = module.classes[0]
#     assert isinstance(cls, Class)
#     assert is_staticmethod(cls.functions[0])
