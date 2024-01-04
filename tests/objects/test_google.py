import ast

from mkapi.objects import Attribute


def test_parse(google):
    name = "module_level_variable2"
    node = google.get(name)
    assert isinstance(node, Attribute)
    assert isinstance(node.docstring, str)
    assert node.docstring.startswith("Module level")
    assert node.docstring.endswith("by a colon.")
    assert isinstance(node.type, ast.Name)
    assert node.type.id == "int"
