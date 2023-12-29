from dataclasses import dataclass

from examples.styles import google
from mkapi.core.base import Base
from mkapi.inspect.attribute import get_attributes, get_description, getsource_dedent
from mkapi.inspect.typing import type_string


def test_getsource_dedent():
    src = getsource_dedent(Base)
    assert src.startswith("@dataclass\nclass Base:\n")
    src = getsource_dedent(google.ExampleClass)
    assert src.startswith("class ExampleClass:\n")


class A:
    def __init__(self):
        self.x: int = 1  #: Doc comment *inline* with attribute.
        #: list of str: Doc comment *before* attribute, with type specified.
        self.y = ["123", "abc"]
        self.a = "dummy"
        self.z: tuple[list[int], dict[str, list[float]]] = (
            [1, 2, 3],
            {"a": [1.2]},
        )
        """Docstring *after* attribute, with type specified.

        Multiple paragraphs are supported."""


def test_class_attribute():
    attrs = get_attributes(A)
    for k, (name, (type_, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y", "a", "z"][k]
        assert markdown.startswith(["Doc ", "list of", "", "Docstring *after*"][k])
        assert markdown.endswith(["attribute.", "specified.", "", "supported."][k])
        if k == 0:
            assert type_ == "int"
        if k == 1:
            assert type_ is None
        if k == 2:
            assert not markdown
        if k == 3:
            x = type_string(type_)
            assert x == "tuple[list[int], dict[str, list[float]]]"
            assert ".\n\nM" in markdown


class B:
    def __init__(self):
        self.x: int = 1
        self.y = ["123", "abc"]


def test_class_attribute_without_desc():
    attrs = get_attributes(B)
    for k, (name, (_, markdown)) in enumerate(attrs.items()):
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

    def func(self):
        pass


def test_dataclass_attribute():
    attrs = get_attributes(C)
    for k, (name, (type_, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y", "z"][k]
        assert markdown == ["int", "A", "B\n\nend."][k]
        if k == 0:
            assert type_ is int


def test_dataclass_ast_parse():
    import ast
    import inspect

    x = C
    s = inspect.getsource(x)
    print(s)
    n = ast.parse(s)
    print(n)
    assert 0


@dataclass
class D:
    x: int
    y: list[str]


def test_dataclass_attribute_without_desc():
    attrs = get_attributes(D)
    for k, (name, (type_, markdown)) in enumerate(attrs.items()):
        assert name == ["x", "y"][k]
        assert markdown == ""
        if k == 0:
            assert type_ is int
        if k == 1:
            x = type_string(type_)
            assert x == "list[str]"


def test_module_attribute():
    attrs = get_attributes(google)  # type:ignore
    for k, (name, (type_, markdown)) in enumerate(attrs.items()):
        if k == 0:
            assert name == "first_attribute"
            assert type_ == "int"
            assert markdown.startswith("The first module level attribute.")
        if k == 1:
            assert name == "second_attribute"
            assert type_ is None
            assert markdown.startswith("str: The second module level attribute.")
        if k == 2:
            assert name == "third_attribute"
            assert type_string(type_) == "list[int]"
            assert markdown.startswith("The third module level attribute.")
            assert markdown.endswith("supported.")


def test_one_line_docstring():
    lines = ["x = 1", "'''docstring'''"]
    assert get_description(lines, 1) == "docstring"


def test_module_attribute_tye():
    from mkapi.core import renderer

    assert get_attributes(renderer)["renderer"][0] is renderer.Renderer  # type: ignore


class E:
    def __init__(self):
        self.a: int = 0  #: attr-a
        self.b: "E" = self  #: attr-b

    def func(self):
        pass


def test_multiple_assignments():
    attrs = get_attributes(E)
    assert attrs["a"] == ("int", "attr-a")
    assert attrs["b"] == (E, "attr-b")
