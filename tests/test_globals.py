import ast

import pytest

from mkapi.globals import (
    Global,
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    get_all,
    get_fullname,
    get_globals,
    resolve,
)
from mkapi.objects import _create_module
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


@pytest.mark.parametrize(
    ("name", "fullname"),
    [
        ("Halo", "halo.halo.Halo"),
        ("tqdm", "tqdm.std.tqdm"),
        ("Config", "mkdocs.config.base.Config"),
        ("MkAPIConfig", "mkapi.plugins.MkAPIConfig"),
    ],
)
def test_get_globals(name, fullname):
    x = get_globals("mkapi.plugins")
    n = get_by_name(x.names, name)
    assert n
    assert n.fullname == fullname


def test_get_globals_cache():
    a = get_globals("mkapi.plugins")
    b = get_globals("mkapi.plugins")
    assert a is b
    c = get_by_name(a.names, "Halo")
    d = get_by_name(b.names, "Halo")
    assert c
    assert c is d


def test_get_all():
    name = "tqdm"
    x = get_all(name)
    assert x["tqdm"] == "tqdm.std.tqdm"
    assert x["main"] == "tqdm.cli.main"
    assert x["TqdmTypeError"] == "tqdm.std.TqdmTypeError"
    assert not get_all("__invalid__")


def test_module():
    name = "mkapi.plugins"
    g = get_globals(name)
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    assert module
    members = module.classes + module.functions + module.attributes
    for member in members:
        x = get_by_name(g.names, member.name.str)
        assert isinstance(x, Global)
        assert x.fullname == member.fullname.str
    assert len(members) == len([x for x in g.names if isinstance(x, Global)])


def test_get_fullname():
    x = get_fullname("MkDocsPage", "mkapi.plugins")
    assert x == "mkdocs.structure.pages.Page"
    x = get_fullname("config_options.Type", "mkapi.plugins")
    assert x == "mkdocs.config.config_options.Type"
    x = get_fullname("config_options.XXX", "mkapi.plugins")
    assert x is None
    x = get_fullname("jinja2.Template", "mkdocs.plugins")
    assert x == "jinja2.environment.Template"
    x = get_fullname("Object", "mkapi.objects")
    assert x == "mkapi.objects.Object"
    x = get_fullname("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = get_fullname("mkapi.objects.Object", "mkapi.objects")
    assert x == "mkapi.objects.Object"


# TODO: get_fullname: import ast -> get ast.AST
