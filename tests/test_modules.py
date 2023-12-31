import pytest

from mkapi import config
from mkapi.modules import Module, cache, find_submodules, get_module


@pytest.fixture(scope="module")
def module():
    return get_module("mkdocs")


def test_get_module(module: Module):
    assert module.is_package()
    assert len(find_submodules(module)) > 0
    module = get_module("mkdocs.structure.files")
    assert not module.is_package()
    assert not find_submodules(module)
    assert module.mtime > 1703851000
    assert module.path.stem == "files"


def test_iter_submodules(module: Module):
    exclude = config.exclude.copy()
    assert len(list(module)) < 45
    config.exclude.clear()
    assert len(list(module)) > 45
    config.exclude = exclude


def test_get_tree():
    module = get_module("mkdocs.structure.files")
    tree = module.get_tree()
    assert isinstance(tree[0], Module)
    assert tree[1] == []
    module = get_module("mkdocs.structure")
    tree = module.get_tree()
    assert isinstance(tree[0], Module)
    assert len(tree[1])
    assert isinstance(tree[1][0], Module)


def test_cache(module: Module):
    assert "mkdocs" in cache
    assert id(get_module("mkdocs")) == id(module)
