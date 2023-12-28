from collections.abc import Iterator

import pytest

from mkapi.core import postprocess as P
from mkapi.core.node import Node


class A:
    """AAA"""

    @property
    def p(self):
        """ppp"""

    def f(self) -> str:  # type: ignore
        """fff"""

    def g(self) -> int:  # type: ignore
        """ggg

        aaa

        Returns:
            value.
        """

    def a(self) -> tuple[int, str]:  # type: ignore
        """aaa"""

    def b(self) -> Iterator[str]:
        """bbb"""
        yield "abc"

    class B:
        """BBB"""


@pytest.fixture()
def node():
    return Node(A)


def test_transform_property(node: Node):
    P.transform_property(node)
    section = node.docstring["Attributes"]
    assert "p" in section
    assert "f" in node


def test_get_type(node: Node):
    assert P.get_type(node).name == ""
    assert P.get_type(node["f"]).name == "str"
    assert P.get_type(node["g"]).name == "int"
    assert P.get_type(node["a"]).name == "(int, str)"
    assert P.get_type(node["b"]).name == "str"
    node["g"].docstring.sections[1]


def test_transform_class(node: Node):
    P.transform(node)
    section = node.docstring["Methods"]
    q = A.__qualname__
    for name in "fgab":
        assert name in section
        item = section[name]
        item.markdown = name * 3
        item.html.startswith(f'<a href="#{q}.{name}">{name}</a>')
    section = node.docstring["Classes"]
    assert "B" in section
    item = section["B"].markdown == "BBB"
    node = Node(A.B)
    P.transform_class(node)


def test_transform_module(module):
    node = Node(module)
    P.transform(node, ["link"])
    q = module.__name__
    section = node.docstring["Functions"]
    assert "add" in section
    item = section["add"]
    item.markdown.startswith("Returns")
    item.html.startswith(f'<a href="#{q}.add">add</a>')
    assert "gen" in section
    section = node.docstring["Classes"]
    assert "ExampleClass" in section
    assert "ExampleDataClass" in section


def test_link_from_toc():
    from examples.styles.google import ExampleClass

    node = Node(ExampleClass)
    assert len(node.docstring.sections) == 4
    P.transform(node)
    assert len(node.docstring.sections) == 5
    assert "Methods" in node.docstring
    section = node.docstring["Methods"]
    html = section.items[0].html
    assert '<a href="#examples.styles.google.ExampleClass.message">' in html
