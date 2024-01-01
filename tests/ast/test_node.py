import ast
from ast import Module

import pytest

from mkapi.ast.node import (
    get_assign_names,
    get_assign_nodes,
    get_by_name,
    get_definition_nodes,
    get_docstring,
    get_import_names,
    get_name,
    get_names,
    iter_import_nodes,
)
from mkapi.utils import get_module_node


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
    names = get_import_names(module)
    assert "logging" in names
    assert names["logging"] == "logging"
    assert "PurePath" in names
    assert names["PurePath"] == "pathlib.PurePath"
    assert "urlquote" in names
    assert names["urlquote"] == "urllib.parse.quote"


def test_get_by_name(def_nodes):
    node = get_by_name(def_nodes, "get_files")
    assert isinstance(node, ast.FunctionDef)
    assert node.name == "get_files"
    node = get_by_name(def_nodes, "InclusionLevel")
    assert isinstance(node, ast.ClassDef)
    assert get_name(node) == "InclusionLevel"
    nodes = get_assign_nodes(node)
    node = get_by_name(nodes, "EXCLUDED")
    assert isinstance(node, ast.Assign)
    assert get_name(node) == "EXCLUDED"


@pytest.fixture(scope="module")
def def_nodes(module: Module):
    return get_definition_nodes(module)


def test_get_definition_nodes(def_nodes):
    assert any(node.name == "get_files" for node in def_nodes)
    assert any(node.name == "Files" for node in def_nodes)


def test_get_assign_names(module: Module, def_nodes):
    names = get_assign_names(module)
    assert names["log"] is not None
    assert names["log"].startswith("logging.getLogger")
    node = get_by_name(def_nodes, "InclusionLevel")
    assert isinstance(node, ast.ClassDef)
    names = get_assign_names(node)
    assert names["NOT_IN_NAV"] is not None
    assert names["NOT_IN_NAV"] == "-1"


def test_get_names(module: Module, def_nodes):
    names = get_names(module)
    assert names["Callable"] == "typing.Callable"
    assert names["File"] == ".File"
    assert names["get_files"] == ".get_files"
    assert names["log"] == ".log"
    node = get_by_name(def_nodes, "File")
    assert isinstance(node, ast.ClassDef)
    names = get_names(node)
    assert names["src_path"] == ".src_path"
    assert names["url"] == ".url"


def test_get_docstring(def_nodes):
    node = get_by_name(def_nodes, "get_files")
    assert isinstance(node, ast.FunctionDef)
    doc = get_docstring(node)
    assert isinstance(doc, str)
    assert doc.startswith("Walk the `docs_dir`")
    with pytest.raises(TypeError):
        get_docstring(node.args)  # type: ignore
    node = get_by_name(def_nodes, "InclusionLevel")
    assert isinstance(node, ast.ClassDef)
    nodes = get_assign_nodes(node)
    node = get_by_name(nodes, "INCLUDED")
    doc = get_docstring(node)  # type: ignore
    assert isinstance(doc, str)
    assert doc.startswith("The file is part of the site.")
