import ast

import pytest

from mkapi.globals import (
    Global,
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    _iter_objects_from_all,
    get_all,
    get_all_from_importlib,
    get_fullname,
    get_globals,
    get_link_from_type,
    get_link_from_type_string,
    iter_identifiers,
    resolve,
)
from mkapi.objects import create_module
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
    assert resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert resolve("polars.col") == "polars.functions.col"
    assert resolve("polars.row") is None
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


def test_get_globals_polars():
    x = get_globals("polars.dataframe.frame")
    n = get_by_name(x.names, "Workbook")
    assert n


def test_get_globals_schemdraw():
    from schemdraw.elements.cables import Element2Term, Segment  # type: ignore

    x = get_globals("schemdraw.elements.cables")
    n = get_by_name(x.names, "Segment")
    assert n
    a = f"{Segment.__module__}.{Segment.__name__}"
    assert n.fullname == a
    n = get_by_name(x.names, "Element2Term")
    assert n
    a = f"{Element2Term.__module__}.{Element2Term.__name__}"
    assert n.fullname == a


def test_get_globals_cache():
    a = get_globals("mkapi.plugins")
    b = get_globals("mkapi.plugins")
    assert a is b
    c = get_by_name(a.names, "Halo")
    d = get_by_name(b.names, "Halo")
    assert c
    assert c is d


def test_module():
    name = "mkapi.plugins"
    g = get_globals(name)
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    members = module.classes + module.functions + module.attributes
    for member in members:
        x = get_by_name(g.names, member.name)
        assert isinstance(x, Global)
        assert x.fullname == member.fullname
    assert len(members) == len([x for x in g.names if isinstance(x, Global)])


def test_get_fullname():
    x = get_fullname("mkapi.plugins", "MkDocsPage")
    assert x == "mkdocs.structure.pages.Page"
    x = get_fullname("mkapi.plugins", "config_options.Type")
    assert x == "mkdocs.config.config_options.Type"
    x = get_fullname("mkapi.plugins", "config_options.XXX")
    assert x is None
    x = get_fullname("mkdocs.plugins", "jinja2.Template")
    assert x == "jinja2.environment.Template"
    x = get_fullname("mkapi.objects", "Object")
    assert x == "mkapi.objects.Object"
    x = get_fullname("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = get_fullname("mkapi.objects", "mkapi.objects.Object")
    assert x == "mkapi.objects.Object"
    x = get_fullname("polars.dataframe.frame", "DataType")
    assert x == "polars.datatypes.classes.DataType"
    x = get_fullname("polars.dataframe.frame", "Workbook")
    assert x == "xlsxwriter.Workbook"


def test_get_link_from_type():
    x = get_link_from_type("mkapi.objects", "Object")
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_link_from_type("mkapi.objects", "Object.__repr__")
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.objects.Object.__repr__]" in x
    x = get_link_from_type("mkapi.plugins", "MkDocsPage")
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"
    x = get_link_from_type("mkdocs.plugins", "jinja2.Template")
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x
    x = get_link_from_type("polars", "DataFrame")
    assert x == "[DataFrame][__mkapi__.polars.dataframe.frame.DataFrame]"
    assert get_link_from_type("mkapi.objects", "str") == "str"
    assert get_link_from_type("mkapi.objects", "None") == "None"
    x = get_link_from_type("mkapi.objects", "mkapi.objects", is_object=True)
    assert x == "[mkapi][__mkapi__.mkapi]..[objects][__mkapi__.mkapi.objects]"


def test_iter_identifiers():
    x = "1"
    assert next(iter_identifiers(x)) == ("1", False)
    x = "a1"
    assert next(iter_identifiers(x)) == ("a1", True)
    x = "a,b"
    assert list(iter_identifiers(x)) == [("a", True), (",", False), ("b", True)]
    x = "dict, Sequence, ndarray, 'Series', or pandas.DataFrame."
    x = list(iter_identifiers(x))
    assert ("dict", True) in x
    assert ("Sequence", True) in x
    assert ("'Series'", False) in x
    assert ("pandas.DataFrame", True) in x


def test_get_link_from_type_string():
    f = get_link_from_type_string
    x = f("mkapi.objects", "1 Object or Class.")
    assert "1 [Object][__mkapi__.mkapi.objects.Object] " in x
    assert "or [Class][__mkapi__.mkapi.objects.Class]." in x


def test_all():
    assert get_fullname("polars", "exceptions") != "polars.exceptions"
    assert get_fullname("polars", "api") == "polars.api"


def test_iter_objects_from_all():
    x = list(_iter_objects_from_all("polars"))
    assert "polars.DataFrame" in x
    assert "polars.first" in x


def test_get_all():
    x = get_all("polars")
    assert x["api"] == "polars.api"
    assert x["ArrowError"] == "polars.exceptions.ArrowError"


def test_get_all_from_importlib():
    assert get_all_from_importlib("altair")
