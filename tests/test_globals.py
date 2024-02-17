import ast

import pytest

from mkapi.globals import (
    Object,
    _iter_imports_from_import,
    _iter_imports_from_import_from,
    _iter_objects,
    get_all,
    get_fullname,
    get_globals,
    resolve,
)
from mkapi.objects import _create_module
from mkapi.utils import get_by_name, get_module_node


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
    n = get_by_name(x, name)
    assert n
    assert n.fullname == fullname


def test_get_globals_cache():
    a = get_globals("mkapi.plugins")
    b = get_globals("mkapi.plugins")
    assert a is b
    c = get_by_name(a, "Halo")
    d = get_by_name(b, "Halo")
    assert c
    assert c is d


def test_get_all():
    name = "tqdm"
    x = get_all(name)
    assert x["tqdm"] == "tqdm.std.tqdm"
    assert x["main"] == "tqdm.cli.main"
    assert x["TqdmTypeError"] == "tqdm.std.TqdmTypeError"
    assert not get_all("__invalid__")


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
