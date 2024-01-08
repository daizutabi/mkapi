from mkapi.docstrings import (
    _iter_items,
    _iter_sections,
    iter_items,
    parse,
    split_item,
    split_section,
    split_without_name,
)
from mkapi.objects import Module


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


def test_iter_sections(google: Module):
    doc = google.docstring
    assert isinstance(doc, str)
    sections = list(_iter_sections(doc, "google"))
    assert len(sections) == 6
    assert sections[0][1].startswith("Example Google")
    assert sections[0][1].endswith("indented text.")
    assert sections[1][0] == "Examples"
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


def test_iter_items(google: Module):
    doc = google.get("module_level_function").docstring  # type: ignore
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[1][1]
    items = list(_iter_items(section))
    assert len(items) == 4
    assert items[0].startswith("param1")
    assert items[1].startswith("param2")
    assert items[2].startswith("*args")
    assert items[3].startswith("**kwargs")
    doc = google.docstring
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[3][1]
    items = list(_iter_items(section))
    assert len(items) == 1
    assert items[0].startswith("module_")


def test_split_item(google: Module):
    doc = google.get("module_level_function").docstring  # type: ignore
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


def test_iter_items_class(google: Module):
    doc = google.get("ExampleClass").docstring  # type: ignore
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[1][1]
    x = list(iter_items(section, "google"))
    assert x[0].name == "attr1"
    assert x[0].type == "str"
    assert x[0].text == "Description of `attr1`."
    assert x[1].name == "attr2"
    assert x[1].type == ":obj:`int`, optional"
    assert x[1].text == "Description of `attr2`."
    doc = google.get("ExampleClass").get("__init__").docstring  # type: ignore
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[2][1]
    x = list(iter_items(section, "google"))
    assert x[0].name == "param1"
    assert x[0].type == "str"
    assert x[0].text == "Description of `param1`."
    assert x[1].text == "Description of `param2`. Multiple\nlines are supported."


def test_split_without_name(google: Module):
    doc = google.get("module_level_function").docstring  # type: ignore
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "google"))[2][1]
    x = split_without_name(section, "google")
    assert x[0] == "bool"
    assert x[1].startswith("True if")
    assert x[1].endswith("    }")


def test_repr(google: Module):
    r = repr(parse(google.docstring, "google"))  # type: ignore
    assert r == "Docstring(num_sections=6)"


def test_iter_items_raises(google: Module):
    doc = google.get("module_level_function").docstring  # type: ignore
    assert isinstance(doc, str)
    name, section = list(_iter_sections(doc, "google"))[3]
    assert name == "Raises"
    items = list(iter_items(section, "google", name))
    assert len(items) == 2
    assert items[0].type == items[0].name == "AttributeError"
    assert items[1].type == items[1].name == "ValueError"
