import typing
from typing import Dict, List

from mkapi.core import signature
from mkapi.core.attribute import get_class_attributes


class A:
    def __init__(self):
        self.x: int = 1  #: Doc comment *inline* with attribute.
        #: list of str: Doc comment *before* attribute, with type specified.
        self.y = ["123", "abc"]
        self.z: typing.Tuple[List[int], Dict[str, List[float]]] = (
            [1, 2, 3],
            {"a": [1.2]},
        )
        """Docstring *after* attribute, with type specified.

        Multiple paragraphs are supported."""


def test_class_attribute():
    attrs = get_class_attributes(A)
    for k, (name, doc) in enumerate(attrs.items()):
        assert name == ["x", "y", "z"][k]
        assert doc[1].startswith(["Doc ", "list of", "Docstring *after*"][k])
        assert doc[1].endswith(["attribute.", "specified.", "supported."][k])
        if k == 0:
            assert doc[0] is int
        elif k == 1:
            assert doc[0] is None
        elif k == 2:
            x = signature.to_string(doc[0])
            assert x == "(list of int, dict(str: list of float))"


class B:
    def __init__(self):
        self.x: int = 1
        self.y = ["123", "abc"]


def test_class_attribute_without_desc():
    attrs = get_class_attributes(B)
    for k, (name, doc) in enumerate(attrs.items()):
        assert name == ["x", "y"][k]
        assert doc[1] == ""
