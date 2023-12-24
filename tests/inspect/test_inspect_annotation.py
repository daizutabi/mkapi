import inspect

import pytest

empty = inspect.Parameter.empty


def test_inspect_func_standard():
    print(type(int) is type)
    print(type(list[int]) is type)
    print(type(inspect.Parameter) is type)
    pytest.fail("debug")
