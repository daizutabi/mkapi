import inspect
from collections.abc import Callable

import pytest

from mkapi.inspect.signature import (
    Signature,
    a_of_b,
    get_parameters,
    get_signature,
    to_string,
)


def test_get_parameters_error():
    with pytest.raises(TypeError):
        get_parameters(1)


def test_get_parameters_function(add, gen):
    # parameters, defaults = get_parameters(add)
    # assert len(parameters) == 2
    # x, y = parameters
    # assert x.name == "x"
    # assert x.type.name == "int"
    # assert y.name == "y"
    # assert y.type.name == "int, optional"
    # assert defaults["x"] is inspect.Parameter.empty
    # assert defaults["y"] == "1"
    signature = inspect.signature(gen)
    assert signature.parameters["n"].annotation == inspect.Parameter.empty
    signature = inspect.signature(add)
    for x in dir(signature.parameters["x"].annotation):
        print(x)
    pytest.fail("debug")


def test_function(add):
    s = Signature(add)
    assert str(s) == "(x, y=1)"

    assert "x" in s
    assert s.parameters["x"].to_tuple()[1] == "int"
    assert s.parameters["y"].to_tuple()[1] == "int, optional"
    assert s.returns == "int"


def test_generator(gen):
    s = Signature(gen)
    assert "n" in s
    assert s.parameters["n"].to_tuple()[1] == ""
    assert s.yields == "str"


def test_class(ExampleClass):  # noqa: N803
    s = Signature(ExampleClass)
    # assert s.parameters["x"].to_tuple()[1] == "list of int"
    # assert s.parameters["y"].to_tuple()[1] == "(str, int)"
    print(s.parameters["x"])
    assert 0


def test_dataclass(ExampleDataClass):  # noqa: N803
    s = Signature(ExampleDataClass)
    assert s.attributes["x"].to_tuple()[1] == "int"
    assert s.attributes["y"].to_tuple()[1] == "int"


def test_to_string():
    assert to_string(list) == "list"
    assert to_string(tuple) == "tuple"
    assert to_string(dict) == "dict"


def test_a_of_b():
    assert a_of_b(list) == "list"
    assert a_of_b(list[list]) == "list of list"
    assert a_of_b(list[dict]) == "list of dict"

    to_string(Callable[[int, int], int])


def test_var():
    def func(x, *args, **kwargs):
        return x, args, kwargs

    s = get_signature(func)
    assert s.parameters.items[1].name == "*args"
    assert s.parameters.items[2].name == "**kwargs"
