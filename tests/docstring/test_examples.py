import pytest

from mkapi.ast import Module
from mkapi.docstring import iter_sections, split_section


def test_split_section_heading():
    f = split_section
    for style in ["google", "numpy"]:
        assert f("A", style) == ("", "A")  # type: ignore
    assert f("A:\n    a\n    b", "google") == ("A", "a\nb")
    assert f("A\n    a\n    b", "google") == ("", "A\n    a\n    b")
    assert f("A\n---\na\nb", "numpy") == ("A", "a\nb")
    assert f("A\n---\n  a\n  b", "numpy") == ("A", "a\nb")
    assert f("A\n  a\n  b", "numpy") == ("", "A\n  a\n  b")


def test_iter_sections_short():
    sections = list(iter_sections("", "google"))
    assert sections == []
    sections = list(iter_sections("x", "google"))
    assert sections == [("", "x")]
    sections = list(iter_sections("x\n", "google"))
    assert sections == [("", "x")]
    sections = list(iter_sections("x\n\n", "google"))
    assert sections == [("", "x")]


@pytest.mark.parametrize("style", ["google", "numpy"])
def test_iter_sections_google(style, google: Module, numpy: Module):
    doc = google.docstring if style == "google" else numpy.docstring
    assert isinstance(doc, str)
    sections = list(iter_sections(doc, style))
    if style == "google":
        assert len(sections) == 7
        assert sections[0][1].startswith("Example Google")
        assert sections[0][1].endswith("docstrings.")
        assert sections[1][1].startswith("This module")
        assert sections[1][1].endswith("indented text.")
        assert sections[2][0] == "Examples"
        assert sections[2][1].startswith("Examples can be")
        assert sections[2][1].endswith("google.py")
        assert sections[3][1].startswith("Section breaks")
        assert sections[3][1].endswith("section starts.")
        assert sections[4][0] == "Attributes"
        assert sections[4][1].startswith("module_level_")
        assert sections[4][1].endswith("with it.")
        assert sections[5][0] == "Todo"
        assert sections[5][1].startswith("* For")
        assert sections[5][1].endswith("extension")
        assert sections[6][1].startswith("..")
        assert sections[6][1].endswith(".html")
    else:
        assert len(sections) == 8
        assert sections[0][1].startswith("Example NumPy")
        assert sections[0][1].endswith("docstrings.")
        assert sections[1][1].startswith("This module")
        assert sections[1][1].endswith("equal length.")
        assert sections[2][0] == "Examples"
        assert sections[2][1].startswith("Examples can be")
        assert sections[2][1].endswith("numpy.py")
        assert sections[3][1].startswith("Section breaks")
        assert sections[3][1].endswith("be\nindented:")
        assert sections[4][0] == "Notes"
        assert sections[4][1].startswith("This is an")
        assert sections[4][1].endswith("surrounding text.")
        assert sections[5][1].startswith("If a section")
        assert sections[5][1].endswith("unindented text.")
        assert sections[6][0] == "Attributes"
        assert sections[6][1].startswith("module_level")
        assert sections[6][1].endswith("with it.")
        assert sections[7][1].startswith("..")
        assert sections[7][1].endswith(".rst.txt")
