import typing
from dataclasses import dataclass
from typing import Dict, List

from examples import google_style
from mkapi.core import signature
from mkapi.core.attribute import get_attributes, get_description


class A:
    def __init__(self):
        self.x: int = 1  #: Doc comment *inline* with attribute.
        #: list of str: Doc comment *before* attribute, with type specified.
        self.y = ["123", "abc"]
        self.a = "dummy"
        self.z: typing.Tuple[List[int], Dict[str, List[float]]] = (
            [1, 2, 3],
            {"a": [1.2]},
        )
        """Docstring *after* attribute, with type specified.

        Multiple paragraphs are supported."""


def test_class_attribute():
    attrs = get_attributes(A)
    assert attrs
    for k, (name, (type, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y", "a", "z"][k]
        assert markdown.startswith(["Doc ", "list of", "", "Docstring *after*"][k])
        assert markdown.endswith(["attribute.", "specified.", "", "supported."][k])
        if k == 0:
            assert type is int
        elif k == 1:
            assert type is None
        elif k == 2:
            assert not markdown
        elif k == 3:
            x = signature.to_string(type)
            assert x == "(list of int, dict(str: list of float))"


class B:
    def __init__(self):
        self.x: int = 1
        self.y = ["123", "abc"]


def test_class_attribute_without_desc():
    attrs = get_attributes(B)
    for k, (name, (type, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y"][k]
        assert markdown == ""


@dataclass
class C:
    x: int  #: int
    #: A
    y: A
    z: B
    """B

    end.
    """


def test_dataclass_attribute():
    attrs = get_attributes(C)
    for k, (name, (type, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y", "z"][k]
        assert markdown == ["int", "A", "B\n\nend."][k]
        if k == 0:
            assert type is int


@dataclass
class D:
    x: int
    y: List[str]


def test_dataclass_attribute_without_desc():
    attrs = get_attributes(D)
    for k, (name, (type, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y"][k]
        assert markdown == ""
        if k == 0:
            assert type is int
        elif k == 1:
            x = signature.to_string(type)
            assert x == "list of str"


def test_module_attribute():
    attrs = get_attributes(google_style)
    for k, (name, (type, markdown)) in enumerate(attrs.items()):
        if k == 0:
            assert name == "first_attribute"
            assert type is int
            assert markdown.startswith("The first module level attribute.")
        if k == 1:
            assert name == "second_attribute"
            assert type is None
            assert markdown.startswith("str: The second module level attribute.")
        if k == 2:
            assert name == "third_attribute"
            assert signature.to_string(type) == "list of int"
            assert markdown.startswith("The third module level attribute.")
            assert markdown.endswith("supported.")


def test_one_line_docstring():
    lines = ["x = 1", "'''docstring'''"]
    assert get_description(lines, 1) == "docstring"


def test_module_attribute_tye():
    from mkapi.core import renderer

    assert get_attributes(renderer)["renderer"][0] is renderer.Renderer


class E:
    def __init__(self):
        self.a: int = 0  #: a
        self.b: str = "b"  #: b

    def func(self):
        self.a, self.b = 1, "x"


def test_multiple_assignments():
    attrs = get_attributes(E)
    assert attrs['a'] == (int, 'a')
    assert attrs['b'] == (str, 'b')
