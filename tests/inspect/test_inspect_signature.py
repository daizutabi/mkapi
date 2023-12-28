import inspect

import pytest

from mkapi.core.node import Node
from mkapi.core.page import Page
from mkapi.inspect.signature import Signature, get_parameters, get_signature


def test_get_parameters_error():
    with pytest.raises(TypeError):
        get_parameters(1)


def test_get_parameters_function(add):
    parameters, defaults = get_parameters(add)
    assert len(parameters) == 2
    x, y = parameters
    assert x.name == "x"
    assert x.type.name == "int"
    assert y.name == "y"
    assert y.type.name == "int, optional"
    assert defaults["x"] is inspect.Parameter.empty
    assert defaults["y"] == "1"


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
    # assert s.parameters["n"].to_tuple()[1] == ""
    assert s.yields == "str"


def test_class(ExampleClass):  # noqa: N803
    s = Signature(ExampleClass)
    assert s.parameters["x"].to_tuple()[1] == "list[int]"
    # assert s.parameters["y"].to_tuple()[1] == "(str, int)"


def test_dataclass(ExampleDataClass):  # noqa: N803
    s = Signature(ExampleDataClass)
    assert s.attributes["x"].to_tuple()[1] == "int"
    assert s.attributes["y"].to_tuple()[1] == "int"


def test_var():
    def func(x, *args, **kwargs):
        return x, args, kwargs

    s = get_signature(func)
    assert s.parameters.items[1].name == "*args"
    assert s.parameters.items[2].name == "**kwargs"


def test_get_signature_special():
    s = Signature(Node.__getitem__)
    assert s.parameters.items[0].name == "index"
    assert s.returns == "[Self](!typing.Self)"
    t = "int | str | list[str]"
    assert s.parameters["index"].to_tuple() == ("index", t, "")
