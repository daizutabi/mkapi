from mkapi.core.inspect import Annotation, Signature


def test_function(add):
    s = Signature(add)
    assert str(s) == "(x, y=1)"

    a = Annotation(add)
    assert "x" in a
    assert a["x"] == "int"
    assert a["y"] == "int, optional"
    assert a.returns == "int"


def test_generator(gen):
    a = Annotation(gen)
    assert "n" in a
    assert a["n"] == ""
    assert a.yields == "str"


def test_class(ExampleClass):
    a = Annotation(ExampleClass)
    assert a["x"] == "list of int"
    assert a["y"] == "(str, int)"


def test_dataclass(ExampleDataClass):
    a = Annotation(ExampleDataClass)
    assert a.attributes["x"] == "int"
    assert a.attributes["y"] == "int"


# def test_annotation_dataclass():
#     a = Annotation(A)
#     assert a["x"] == "int"
#     assert a["y"] == "float, optional"
#     assert a.attributes["x"] == "int"
