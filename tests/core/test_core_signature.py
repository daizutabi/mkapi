from mkapi.core.signature import Signature


def test_function(add):
    s = Signature(add)
    assert str(s) == "(x, y=1)"

    assert "x" in s
    assert s.parameters["x"] == "int"
    assert s.parameters["y"] == "int, optional"
    assert s.returns == "int"


def test_generator(gen):
    s = Signature(gen)
    assert "n" in s
    assert s.parameters["n"] == ""
    assert s.yields == "str"


def test_class(ExampleClass):
    s = Signature(ExampleClass)
    assert s.parameters["x"] == "list of int"
    assert s.parameters["y"] == "(str, int)"


def test_dataclass(ExampleDataClass):
    s = Signature(ExampleDataClass)
    assert s.attributes["x"] == "int"
    assert s.attributes["y"] == "int"
