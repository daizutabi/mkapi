import ast
from ast import Module

import pytest

import mkapi.objects
from mkapi.objects import (
    _get_module_node,
    get_module,
    get_object,
    iter_callable_nodes,
    iter_import_nodes,
    iter_imports,
)


def test_get_module_node():
    node = _get_module_node("mkdocs")
    assert isinstance(node, Module)


def test_module_cache():
    node1 = _get_module_node("mkdocs")
    node2 = _get_module_node("mkdocs")
    assert node1 is node2
    module1 = get_module("mkapi")
    module2 = get_module("mkapi")
    assert module1 is module2


@pytest.fixture(scope="module")
def module():
    return _get_module_node("mkdocs.structure.files")


def test_iter_import_nodes(module: Module):
    node = next(iter_import_nodes(module))
    assert isinstance(node, ast.ImportFrom)
    assert len(node.names) == 1
    alias = node.names[0]
    assert node.module == "__future__"
    assert alias.name == "annotations"
    assert alias.asname is None


def test_get_import_names(module: Module):
    it = iter_imports(module)
    names = {im.name: im.fullname for im in it}
    assert "logging" in names
    assert names["logging"] == "logging"
    assert "PurePath" in names
    assert names["PurePath"] == "pathlib.PurePath"
    assert "urlquote" in names
    assert names["urlquote"] == "urllib.parse.quote"


@pytest.fixture(scope="module")
def def_nodes(module: Module):
    return list(iter_callable_nodes(module))


def test_iter_definition_nodes(def_nodes):
    assert any(node.name == "get_files" for node in def_nodes)
    assert any(node.name == "Files" for node in def_nodes)


def test_not_found():
    assert _get_module_node("xxx") is None
    assert get_module("xxx") is None
    assert mkapi.objects.cache_module["xxx"] is None
    assert "xxx" not in mkapi.objects.cache_module_node
    assert get_module("markdown") is not None
    assert "markdown" in mkapi.objects.cache_module
    assert "markdown" in mkapi.objects.cache_module_node


def test_repr():
    module = get_module("mkapi")
    assert repr(module) == "Module(mkapi)"
    module = get_module("mkapi.objects")
    assert repr(module) == "Module(mkapi.objects)"
    obj = get_object("mkapi.objects.Object")
    assert repr(obj) == "Class(Object)"
    obj = get_object("mkapi.plugins.BasePlugin")
    assert repr(obj) == "Class(BasePlugin)"


def test_get_source():
    module = get_module("mkdocs.structure.files")
    assert module
    assert "class File" in module.source
    module = get_module("mkapi.plugins")
    assert module
    cls = module.get("MkAPIConfig")
    assert cls.get_module() is module
    assert cls.get_source().startswith("class MkAPIConfig")
    assert "MkAPIPlugin" in module.get_source()
