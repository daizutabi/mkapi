import os
import sys

import pytest

import mkapi.core.inspect

sys.path.insert(0, os.path.abspath("examples"))


@pytest.fixture(scope="session")
def node():
    return mkapi.core.inspect.get_node("example.google")
