import ast

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.utils import get_module_node


@pytest.fixture(scope="module")
def google():
    return get_module_node("examples.styles.google")


@pytest.fixture(scope="module")
def numpy():
    return get_module_node("examples.styles.numpy")


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
