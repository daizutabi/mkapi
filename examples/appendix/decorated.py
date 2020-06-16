"""Decorator examples."""
import pytest

from appendix.decorator import deco_with_wraps, deco_without_wraps


@deco_without_wraps
def func_without_wraps():
    """Decorated function without `wraps`."""


@deco_with_wraps
def func_with_wraps():
    """Decorated function with `wraps`."""


@deco_with_wraps
@deco_with_wraps
def func_with_wraps_double():
    """Doubly decorated function with `wraps`."""


@pytest.fixture
def fixture():
    """Fixture."""
    yield 1


@pytest.fixture
@deco_with_wraps
def fixture_with_wraps():
    """Fixture."""
    yield 1
