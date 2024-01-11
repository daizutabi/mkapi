import sys
from pathlib import Path

import pytest

from mkapi.objects import load_module


@pytest.fixture(scope="module")
def google():
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    return load_module("examples.styles.example_google")


@pytest.fixture(scope="module")
def numpy():
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    return load_module("examples.styles.example_numpy")
