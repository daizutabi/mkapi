from itertools import product

import pytest

from mkapi.core.base import Base, Inline
from mkapi.core.inherit import get_section, is_complete
from mkapi.core.node import Node


def test_is_complete():
    assert is_complete(Node(Base))
    assert not is_complete(Node(Inline))


@pytest.mark.parametrize(
    ("name", "mode"),
    product(["Parameters", "Attributes"], ["Docstring", "Signature"]),
)
def test_get_section(name, mode):
    def func():
        pass

    section = get_section(Node(func), name, mode)
    assert section.name == name
    assert not section
