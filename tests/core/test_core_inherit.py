from mkapi.core.base import Base, Inline
from mkapi.core.inherit import is_complete
from mkapi.core.node import Node


def test_is_complete():
    assert is_complete(Node(Base))
    assert not is_complete(Node(Inline))
