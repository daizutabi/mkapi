import ast
import sys
from pathlib import Path

import pytest

from mkapi.objects import _get_module_from_node, get_module_path


def get_module(name):
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    path = get_module_path(name)
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    return _get_module_from_node(node)


@pytest.fixture(scope="module")
def google():
    return get_module("examples.styles.example_google")


@pytest.fixture(scope="module")
def numpy():
    return get_module("examples.styles.example_numpy")
