from mkapi.core.base import Docstring
from mkapi.core.docstring import parse_bases
from mkapi.core.inherit import inherit
from mkapi.core.node import get_node
from mkapi.examples import meta
from mkapi.examples.meta import C, F


def test_mro_docstring():
    doc = Docstring()
    parse_bases(doc, C)
    assert len(doc["Bases"].items) == 2
    assert doc["Bases"].items[0].type.markdown == "[examples.meta.B](!examples.meta.B)"
    assert doc["Bases"].items[1].type.markdown == "[examples.meta.A](!examples.meta.A)"

    doc = Docstring()
    parse_bases(doc, F)
    assert len(doc["Bases"].items) == 2
    assert doc["Bases"].items[0].type.markdown == "[examples.meta.E](!examples.meta.E)"
    assert doc["Bases"].items[1].type.markdown == "[examples.meta.D](!examples.meta.D)"


def test_mro_node():
    node = get_node(C)
    assert len(node.members) == 2
    assert node.members[0].object.id == "examples.meta.A.f"
    assert node.members[1].object.id == "examples.meta.C.g"


def test_mro_inherit():
    node = get_node(C)
    inherit(node)
    item = node.members[1].docstring["Parameters"].items[0]
    assert item.description.markdown == "parameter."


def test_mro_module():
    node = get_node(meta)
    assert len(node.members) == 6
