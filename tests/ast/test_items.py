import ast

import pytest

from mkapi.ast.node import Module, get_module, get_module_node


@pytest.fixture(scope="module")
def module():
    node = get_module_node("mkapi.ast.node")
    return get_module(node)


def test_args(module: Module):
    print(module.classes)
    assert 0


def test_attrs(module: Module):
    attrs = module.attrs
    print(attrs)
    assert 0
    # args = get_arguments
