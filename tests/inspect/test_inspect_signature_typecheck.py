import inspect

from examples.typing import current, future


def test_current_annotation():
    signature = inspect.signature(current.func)
    assert signature.parameters["x"].annotation is int


def test_future_annotation():
    signature = inspect.signature(future.func)
    assert signature.parameters["x"].annotation == "int"
