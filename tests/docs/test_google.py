import ast

from mkapi.docs import (
    _iter_items,
    _iter_sections,
    create_doc,
    iter_items,
    merge,
    split_item,
    split_section,
)


def test_split_section():
    f = split_section
    for style in ["google", "numpy"]:
        assert f("A", style) == ("", "A")  # type: ignore
    assert f("A:\n    a\n    b", "google") == ("A", "a\nb")
    assert f("A\n    a\n    b", "google") == ("", "A\n    a\n    b")
    assert f("A\n---\na\nb", "numpy") == ("A", "a\nb")
    assert f("A\n---\n  a\n  b", "numpy") == ("A", "a\nb")
    assert f("A\n  a\n  b", "numpy") == ("", "A\n  a\n  b")


def test_iter_sections_short():
    sections = list(_iter_sections("", "google"))
    assert sections == []
    sections = list(_iter_sections("x", "google"))
    assert sections == [("", "x")]
    sections = list(_iter_sections("x\n", "google"))
    assert sections == [("", "x")]
    sections = list(_iter_sections("x\n\n", "google"))
    assert sections == [("", "x")]


def test_iter_sections(google):
    doc = ast.get_docstring(google)
    assert isinstance(doc, str)
    sections = list(_iter_sections(doc, "google"))
    assert len(sections) == 6
    assert sections[0][1].startswith("Example Google")
    assert sections[0][1].endswith("indented text.")
    assert sections[1][0] == "Example"
    assert sections[1][1].startswith("Examples can be")
    assert sections[1][1].endswith("google.py")
    assert sections[2][1].startswith("Section breaks")
    assert sections[2][1].endswith("section starts.")
    assert sections[3][0] == "Attributes"
    assert sections[3][1].startswith("module_level_")
    assert sections[3][1].endswith("with it.")
    assert sections[4][0] == "Todo"
    assert sections[4][1].startswith("* For")
    assert sections[4][1].endswith("extension")
    assert sections[5][1].startswith("..")
    assert sections[5][1].endswith(".html")


def test_iter_items(google, get):
    doc = ast.get_docstring(google)
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[3][1]
    items = list(_iter_items(section))
    assert len(items) == 1
    assert items[0].startswith("module_")
    doc = get(google, "module_level_function")
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[1][1]
    items = list(_iter_items(section))
    assert len(items) == 4
    assert items[0].startswith("param1")
    assert items[1].startswith("param2")
    assert items[2].startswith("*args")
    assert items[3].startswith("**kwargs")


def test_split_item(google, get):
    doc = get(google, "module_level_function")
    assert isinstance(doc, str)
    sections = list(_iter_sections(doc, "google"))
    section = sections[1][1]
    items = list(_iter_items(section))
    x = split_item(items[0], "google")
    assert x == ("param1", "int", "The first parameter.")
    x = split_item(items[1], "google")
    assert x[:2] == ("param2", ":obj:`str`, optional")
    assert x[2].endswith("should be indented.")
    x = split_item(items[2], "google")
    assert x == ("*args", "", "Variable length argument list.")
    section = sections[3][1]
    items = list(_iter_items(section))
    x = split_item(items[0], "google")
    assert x[:2] == ("AttributeError", "")
    assert x[2].endswith("the interface.")


def test_iter_items_class(google, get, get_node):
    doc = get(google, "ExampleClass")
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[1][1]
    x = list(iter_items(section, "google"))
    assert x[0].name == "attr1"
    assert x[0].type == "str"
    assert x[0].text == "Description of `attr1`."
    assert x[1].name == "attr2"
    assert x[1].type == ":obj:`int`, optional"
    assert x[1].text == "Description of `attr2`."
    doc = get(get_node(google, "ExampleClass"), "__init__")
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[2][1]
    x = list(iter_items(section, "google"))
    assert x[0].name == "param1"
    assert x[0].type == "str"
    assert x[0].text == "Description of `param1`."
    assert x[1].text == "Description of `param2`. Multiple\nlines are supported."


def test_parse(google):
    doc = create_doc(ast.get_docstring(google), "google")  # type: ignore
    assert doc.text.startswith("Example Google style docstrings.")
    assert doc.sections[0].name == "Example"


def test_merge(google, get, get_node):
    a = create_doc(get(google, "ExampleClass"))
    b = create_doc(get(get_node(google, "ExampleClass"), "__init__"))
    doc = merge(a, b)
    assert doc.text
    assert doc.text.startswith("The summary line")
    assert doc.text.endswith("with it.")
    assert len(doc.sections) == 3


def test_repr(google):
    r = repr(create_doc(ast.get_docstring(google), "google"))  # type: ignore
    assert r == "Doc(sections=5)"
