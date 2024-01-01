from ast import Module

from mkapi.utils import find_submodule_names, get_module_node, module_cache


def test_get_module_node():
    node = get_module_node("mkdocs")
    assert isinstance(node, Module)


def test_find_submodule_names():
    names = find_submodule_names("mkdocs")
    assert "mkdocs.commands" in names
    assert "mkdocs.plugins" in names


def test_module_cache():
    node1 = get_module_node("mkdocs")
    node2 = get_module_node("mkdocs")
    assert node1 is node2
