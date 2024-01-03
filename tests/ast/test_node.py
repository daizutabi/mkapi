import ast
from ast import Module

import pytest

from mkapi.ast import (
    get_module,
    get_module_node,
    iter_definition_nodes,
    iter_import_nodes,
    iter_imports,
)


def test_get_module_node():
    node = get_module_node("mkdocs")
    assert isinstance(node, Module)


def test_module_cache():
    node1 = get_module_node("mkdocs")
    node2 = get_module_node("mkdocs")
    assert node1 is node2


@pytest.fixture(scope="module")
def module():
    return get_module_node("mkdocs.structure.files")


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
    return list(iter_definition_nodes(module))


def test_iter_definition_nodes(def_nodes):
    assert any(node.name == "get_files" for node in def_nodes)
    assert any(node.name == "Files" for node in def_nodes)
