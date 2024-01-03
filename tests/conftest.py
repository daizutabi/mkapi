import sys
from pathlib import Path

import pytest

from mkapi.ast import get_module, get_module_node


@pytest.fixture(scope="module")
def google():
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    node = get_module_node("examples.styles.example_google")
    return get_module(node)


@pytest.fixture(scope="module")
def numpy():
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    node = get_module_node("examples.styles.example_numpy")
    return get_module(node)
