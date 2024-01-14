import ast

from mkapi.docstrings import (
    _iter_items,
    _iter_sections,
    iter_items,
    split_item,
    split_section,
)


def test_split_section():
    f = split_section
    assert f("A", "numpy") == ("", "A")  # type: ignore
    assert f("A\n---\na\nb", "numpy") == ("A", "a\nb")
    assert f("A\n---\n  a\n  b", "numpy") == ("A", "a\nb")
    assert f("A\n  a\n  b", "numpy") == ("", "A\n  a\n  b")


def test_iter_sections_short():
    sections = list(_iter_sections("", "numpy"))
    assert sections == []
    sections = list(_iter_sections("x", "numpy"))
    assert sections == [("", "x")]
    sections = list(_iter_sections("x\n", "numpy"))
    assert sections == [("", "x")]
    sections = list(_iter_sections("x\n\n", "numpy"))
    assert sections == [("", "x")]


def test_iter_sections(numpy):
    doc = ast.get_docstring(numpy)
    assert isinstance(doc, str)
    sections = list(_iter_sections(doc, "numpy"))
    assert len(sections) == 7
    assert sections[0][1].startswith("Example NumPy")
    assert sections[0][1].endswith("equal length.")
    assert sections[1][0] == "Examples"
    assert sections[1][1].startswith("Examples can be")
    assert sections[1][1].endswith("numpy.py")
    assert sections[2][1].startswith("Section breaks")
    assert sections[2][1].endswith("be\nindented:")
    assert sections[3][0] == "Notes"
    assert sections[3][1].startswith("This is an")
    assert sections[3][1].endswith("surrounding text.")
    assert sections[4][1].startswith("If a section")
    assert sections[4][1].endswith("unindented text.")
    assert sections[5][0] == "Attributes"
    assert sections[5][1].startswith("module_level")
    assert sections[5][1].endswith("with it.")
    assert sections[6][1].startswith("..")
    assert sections[6][1].endswith(".rst.txt")


def test_iter_items(numpy, get):
    doc = ast.get_docstring(numpy)
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "numpy"))[5][1]
    items = list(_iter_items(section))
    assert len(items) == 1
    assert items[0].startswith("module_")
    doc = get(numpy, "module_level_function")
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "numpy"))[1][1]
    items = list(_iter_items(section))
    assert len(items) == 4
    assert items[0].startswith("param1")
    assert items[1].startswith("param2")
    assert items[2].startswith("*args")
    assert items[3].startswith("**kwargs")


def test_split_item(numpy, get):
    doc = get(numpy, "module_level_function")
    assert isinstance(doc, str)
    sections = list(_iter_sections(doc, "numpy"))
    items = list(_iter_items(sections[1][1]))
    x = split_item(items[0], "numpy")
    assert x == ("param1", "int", "The first parameter.")
    x = split_item(items[1], "numpy")
    assert x[:2] == ("param2", ":obj:`str`, optional")
    assert x[2] == "The second parameter."
    x = split_item(items[2], "numpy")
    assert x == ("*args", "", "Variable length argument list.")
    items = list(_iter_items(sections[3][1]))
    x = split_item(items[0], "numpy")
    assert x[:2] == ("AttributeError", "")
    assert x[2].endswith("the interface.")


def test_iter_items_class(numpy, get, get_node):
    doc = get(numpy, "ExampleClass")
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "numpy"))[1][1]
    x = list(iter_items(section, "numpy"))
    assert x[0][0] == "attr1"
    assert x[0][1].expr.value == "str"  # type: ignore
    assert x[0][2].str == "Description of `attr1`."
    assert x[1][0] == "attr2"
    assert x[1][1].expr.value == ":obj:`int`, optional"  # type: ignore
    assert x[1][2].str == "Description of `attr2`."
    doc = get(get_node(numpy, "ExampleClass"), "__init__")
    assert isinstance(doc, str)
    section = list(_iter_sections(doc, "numpy"))[2][1]
    x = list(iter_items(section, "numpy"))
    assert x[0][0] == "param1"
    assert x[0][1].expr.value == "str"  # type: ignore
    assert x[0][2].str == "Description of `param1`."
    assert x[1][2].str == "Description of `param2`. Multiple\nlines are supported."


def test_iter_items_raises(numpy, get):
    doc = get(numpy, "module_level_function")
    assert isinstance(doc, str)
    name, section = list(_iter_sections(doc, "numpy"))[3]
    assert name == "Raises"
    items = list(iter_items(section, "numpy"))
    assert len(items) == 2
    assert items[0][0] == "AttributeError"  # type: ignore
    assert items[1][0] == "ValueError"  # type: ignore
