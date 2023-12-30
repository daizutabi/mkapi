import ast

import pytest

from mkapi.ast import (
    get_assign_nodes,
    get_by_name,
    get_def_nodes,
    get_docstring,
    get_import_names,
    get_name,
    iter_import_nodes,
)
from mkapi.modules import get_module


@pytest.fixture(scope="module")
def source():
    return get_module("mkdocs.structure.files").source


@pytest.fixture(scope="module")
def module(source):
    return ast.parse(source, type_comments=True)


def test_iter_import_nodes(module):
    node = next(iter_import_nodes(module))
    assert isinstance(node, ast.ImportFrom)
    assert len(node.names) == 1

    alias = node.names[0]
    assert node.module == "__future__"
    assert alias.name == "annotations"
    assert alias.asname is None


def test_get_import_names(module):
    names = get_import_names(module)
    assert (None, "logging", None) in names
    assert ("pathlib", "PurePath", None) in names
    assert ("urllib.parse", "quote", "urlquote") in names


@pytest.fixture(scope="module")
def def_nodes(module):
    return get_def_nodes(module)


def test_get_def_nodes(def_nodes):
    assert any(node.name == "get_files" for node in def_nodes)
    assert any(node.name == "Files" for node in def_nodes)


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


# def test_source(source):
#     print(source)
#     assert 0


# def test_get_assign_nodes(def_nodes):
#     for node in def_nodes:
#         if node.name == "InclusionLevel":
#             nodes = get_assign_nodes(node)
#             for node
#             print(len(nodes))
#     assert 0
