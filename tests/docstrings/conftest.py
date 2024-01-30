import ast
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.utils import get_module_node


def load_module(name):
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    return get_module_node(name)


@pytest.fixture(scope="module")
def google():
    return load_module("examples.styles.example_google")


@pytest.fixture(scope="module")
def numpy():
    return load_module("examples.styles.example_numpy")


@pytest.fixture(scope="module")
def get_node():
    def get_node(node, name):
        for child in iter_child_nodes(node):
            if not isinstance(child, ast.FunctionDef | ast.ClassDef):
                continue
            if child.name == name:
                return child
        raise NameError

    return get_node


@pytest.fixture(scope="module")
def get(get_node):
    def get(node, name):
        return ast.get_docstring(get_node(node, name))

    return get
