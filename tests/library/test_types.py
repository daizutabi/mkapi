from collections.abc import Callable
from types import GenericAlias


def test_callable():
    t = Callable[[], None]
    assert isinstance(t, GenericAlias)
