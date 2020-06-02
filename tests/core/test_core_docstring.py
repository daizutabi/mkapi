from mkapi.core.docstring import parse_docstring


def test_function(add):
    doc = parse_docstring(add)
    assert len(doc.sections) == 6
    assert doc.sections[0].name == ""
    assert doc.sections[0].markdown.startswith("Returns $")
    assert doc.sections[1].name == "Parameters"
    assert doc.sections[1].items[0].name == "x"
    assert doc.sections[1].items[0].type == "int"
    assert doc.sections[1].items[1].name == "y"
    assert doc.sections[1].items[1].type == "int, optional"


def test_class(ExampleClass):
    doc = parse_docstring(ExampleClass)
    assert doc is None
