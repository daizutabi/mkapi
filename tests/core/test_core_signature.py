from typing import Callable, Dict, List, Tuple

from mkapi.core.signature import Signature, a_of_b, get_signature, to_string


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


def test_class(ExampleClass):
    s = Signature(ExampleClass)
    assert s.parameters["x"].to_tuple()[1] == "list of int"
    assert s.parameters["y"].to_tuple()[1] == "(str, int)"


def test_dataclass(ExampleDataClass):
    s = Signature(ExampleDataClass)
    assert s.attributes["x"].to_tuple()[1] == "int"
    assert s.attributes["y"].to_tuple()[1] == "int"


def test_to_string():
    assert to_string(List) == "list"
    assert to_string(Tuple) == "tuple"
    assert to_string(Dict) == "dict"


def test_a_of_b():
    assert a_of_b(List) == "list"
    assert a_of_b(List[List]) == "list of list"
    assert a_of_b(List[Dict]) == "list of dict"

    to_string(Callable[[int, int], int])


def test_var():
    def func(x, *args, **kwargs):
        pass

    s = get_signature(func)
    assert s.parameters.items[1].name == "*args"
    assert s.parameters.items[2].name == "**kwargs"
