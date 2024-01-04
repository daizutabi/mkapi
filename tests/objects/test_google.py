import ast

from mkapi.objects import Attribute, Function, merge_docstring


def test_merge_docstring_attribute(google):
    name = "module_level_variable2"
    node = google.get(name)
    assert isinstance(node, Attribute)
    assert isinstance(node.docstring, str)
    assert node.docstring.startswith("Module level")
    assert node.docstring.endswith("by a colon.")
    assert isinstance(node.type, ast.Name)
    assert node.type.id == "int"


def test_property(google):
    cls = google.get("ExampleClass")
    attr = cls.get("readonly_property")
    assert isinstance(attr, Attribute)
    assert attr.docstring
    assert attr.docstring.startswith("Properties should be")
    assert ast.unparse(attr.type) == "str"  # type: ignore
    attr = cls.get("readwrite_property")
    assert isinstance(attr, Attribute)
    assert attr.docstring
    assert attr.docstring.endswith("mentioned here.")
    assert ast.unparse(attr.type) == "list[str]"  # type: ignore


def test_merge_docstring(google):
    module = google
    merge_docstring(module)
    assert 0
