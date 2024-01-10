import ast

import pytest

import mkapi.ast
import mkapi.objects
from mkapi.ast import iter_callable_nodes, iter_import_nodes
from mkapi.objects import (
    CACHE_MODULE,
    CACHE_OBJECT,
    get_module,
    get_module_path,
    get_object,
    iter_imports,
)


@pytest.fixture(scope="module")
def module():
    path = get_module_path("mkdocs.structure.files")
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


def test_iter_import_nodes(module: ast.Module):
    node = next(iter_import_nodes(module))
    assert isinstance(node, ast.ImportFrom)
    assert len(node.names) == 1
    alias = node.names[0]
    assert node.module == "__future__"
    assert alias.name == "annotations"
    assert alias.asname is None


def test_get_import_names(module: ast.Module):
    it = iter_imports(module)
    names = {im.name: im.fullname for im in it}
    assert "logging" in names
    assert names["logging"] == "logging"
    assert "PurePath" in names
    assert names["PurePath"] == "pathlib.PurePath"
    assert "urlquote" in names
    assert names["urlquote"] == "urllib.parse.quote"


@pytest.fixture(scope="module")
def def_nodes(module: ast.Module):
    return list(iter_callable_nodes(module))


def test_iter_definition_nodes(def_nodes):
    assert any(node.name == "get_files" for node in def_nodes)
    assert any(node.name == "Files" for node in def_nodes)


def test_not_found():
    assert get_module("xxx") is None
    assert mkapi.objects.CACHE_MODULE["xxx"] is None
    assert get_module("markdown")
    assert "markdown" in mkapi.objects.CACHE_MODULE


def test_repr():
    module = get_module("mkapi")
    assert repr(module) == "Module(mkapi)"
    module = get_module("mkapi.objects")
    assert repr(module) == "Module(mkapi.objects)"
    obj = get_object("mkapi.objects.Object")
    assert repr(obj) == "Class(Object)"


def test_get_module_source():
    module = get_module("mkdocs.structure.files")
    assert module
    assert module.source
    assert "class File" in module.source
    module = get_module("mkapi.plugins")
    assert module
    cls = module.get("MkAPIConfig")
    assert cls
    assert cls.get_module() is module
    src = cls.get_source()
    assert src
    assert src.startswith("class MkAPIConfig")
    src = module.get_source()
    assert src
    assert "MkAPIPlugin" in src


def test_get_module_from_object():
    module = get_module("mkdocs.structure.files")
    assert module
    c = module.classes[1]
    m = c.get_module()
    assert module is m


def test_get_fullname(google):
    c = google.get_class("ExampleClass")
    f = c.get_function("example_method")
    assert c.get_fullname() == "examples.styles.example_google.ExampleClass"
    name = "examples.styles.example_google.ExampleClass.example_method"
    assert f.get_fullname() == name


def test_cache():
    CACHE_MODULE.clear()
    CACHE_OBJECT.clear()
    module = get_module("mkapi.objects")
    c = get_object("mkapi.objects.Object")
    f = get_object("mkapi.objects.Module.get_class")
    assert c
    assert c.get_module() is module
    assert f
    assert f.get_module() is module
    c2 = get_object("mkapi.objects.Object")
    f2 = get_object("mkapi.objects.Module.get_class")
    assert c is c2
    assert f is f2

    m1 = get_module("mkdocs.structure.files")
    m2 = get_module("mkdocs.structure.files")
    assert m1 is m2
    CACHE_MODULE.clear()
    m3 = get_module("mkdocs.structure.files")
    m4 = get_module("mkdocs.structure.files")
    assert m2 is not m3
    assert m3 is m4


def test_module_kind():
    module = get_module("mkapi")
    assert module
    assert module.kind == "package"
    module = get_module("mkapi.objects")
    assert module
    assert module.kind == "module"


def test_get_fullname_with_attr():
    module = get_module("mkapi.plugins")
    assert module
    name = module.get_fullname("config_options.Type")
    assert name == "mkdocs.config.config_options.Type"
