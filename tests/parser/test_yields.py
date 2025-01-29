import ast

from astdoc.ast import iter_identifiers
from astdoc.node import get_fullname_from_module
from astdoc.object import Function, get_object


def test_return_type_name():
    n = get_fullname_from_module("collections.abc.Iterator", "examples.parser")
    assert n == "collections.abc.Iterator"
    n = get_fullname_from_module("Generator", "examples.parser")
    assert n == "collections.abc.Generator"


def test_return_type_iterator():
    obj = get_object("examples.parser.iterator")
    assert isinstance(obj, Function)
    node = obj.node.returns
    assert node
    assert next(iter_identifiers(node)) == "collections.abc.Iterator"


def test_return_type_generator():
    obj = get_object("examples.parser.generator")
    assert isinstance(obj, Function)
    node = obj.node.returns
    assert node
    assert next(iter_identifiers(node)) == "Generator"


def test_return_type_iterator_slice():
    obj = get_object("examples.parser.iterator")
    assert isinstance(obj, Function)
    node = obj.node.returns
    assert isinstance(node, ast.Subscript)
    assert isinstance(node.slice, ast.Name)
    assert node.slice.id == "int"


def test_return_type_generator_slice():
    obj = get_object("examples.parser.generator")
    assert isinstance(obj, Function)
    node = obj.node.returns
    assert isinstance(node, ast.Subscript)
    assert isinstance(node.slice, ast.Tuple)
    assert len(node.slice.elts) == 3
    assert isinstance(node.slice.elts[0], ast.Subscript)


def test_return_type_iterator_doc():
    from mkapi.parser import Parser

    parser = Parser.create("examples.parser.iterator")
    assert parser
    doc = parser.parse_doc()
    assert doc.sections
    section = doc.sections[0]
    assert section.name == "Yields"
    assert section.items
    item = section.items[0]
    assert item.type == "int"


def test_return_type_generator_doc():
    from mkapi.parser import Parser

    parser = Parser.create("examples.parser.generator")
    assert parser
    doc = parser.parse_doc()
    assert doc.sections
    section = doc.sections[0]
    assert section.name == "Yields"
    assert section.items
    item = section.items[0]
    t = "list[[PrivateAttribute][__mkapi__.examples.parser.PrivateAttribute]]"
    assert item.type == t
