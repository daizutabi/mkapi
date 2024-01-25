import ast
import inspect
import re

import pytest

from mkapi.globals import (
    LINK_PATTERN,
    Global,
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    _resolve,
    get_fullname,
    get_globals,
    get_link_from_text,
    get_link_from_type,
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
    assert _resolve("tqdm.tqdm") == "tqdm.std.tqdm"
    assert _resolve("logging.Template") == "string.Template"
    assert _resolve("halo.Halo") == "halo.halo.Halo"
    assert _resolve("jinja2.Template") == "jinja2.environment.Template"
    assert _resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert _resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert _resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"


def test_relative_import():
    """# test module
    from .c import d
    from ..e import f as F
    """
    src = inspect.getdoc(test_relative_import)
    assert src
    node = ast.parse(src)
    x = node.body[0]
    assert isinstance(x, ast.ImportFrom)
    i = next(_iter_imports_from_import_from(x, "x.y.z"))
    assert i == ("d", "x.y.z.c.d")
    x = node.body[1]
    assert isinstance(x, ast.ImportFrom)
    i = next(_iter_imports_from_import_from(x, "x.y.z"))
    assert i == ("F", "x.y.e.f")


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


def test_link_pattern():
    def f(m: re.Match) -> str:
        name = m.group(1)
        if name == "abc":
            return f"[{name}][_{name}]"
        return m.group()

    assert re.search(LINK_PATTERN, "X[abc]Y")
    assert not re.search(LINK_PATTERN, "X[ab c]Y")
    assert re.search(LINK_PATTERN, "X[abc][]Y")
    assert not re.search(LINK_PATTERN, "X[abc](xyz)Y")
    assert not re.search(LINK_PATTERN, "X[abc][xyz]Y")
    assert re.sub(LINK_PATTERN, f, "X[abc]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc[abc]]Y") == "X[abc[abc][_abc]]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab]Y") == "X[ab]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab c]Y") == "X[ab c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc] c]Y") == "X[abc][_abc] c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc](xyz)Y") == "X[abc](xyz)Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][xyz]Y") == "X[abc][xyz]Y"


def test_get_link_from_type():
    x = get_link_from_type("mkapi.objects", "Object")
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_link_from_type("mkapi.objects", "Object.__repr__")
    assert ".[__repr__][__mkapi__.mkapi.objects.Object.__repr__]" in x
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
    assert x == "[mkapi][__mkapi__.mkapi].objects"


def test_get_link_from_text():
    x = get_link_from_text("mkapi.objects", "# title\n[Object]")
    assert x == "# title\n[Object][__mkapi__.mkapi.objects.Object]"
