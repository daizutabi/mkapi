import ast
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_callable_nodes
from mkapi.objects import get_module_path


def get_module(name):
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    path = get_module_path(name)
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


@pytest.fixture(scope="module")
def google():
    return get_module("examples.styles.example_google")


@pytest.fixture(scope="module")
def numpy():
    return get_module("examples.styles.example_numpy")


@pytest.fixture(scope="module")
def get_node():
    def get_node(node, name):
        for child in iter_callable_nodes(node):
            if child.name == name:
                return child
        raise NameError

    return get_node


@pytest.fixture(scope="module")
def get(get_node):
    def get(node, name):
        return ast.get_docstring(get_node(node, name))

    return get
