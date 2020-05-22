import pytest

import mkapi.core.node


@pytest.fixture(scope="session")
def example():
    return mkapi.core.node.get_node("example")
