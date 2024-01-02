import pytest

from mkapi.docstring import (
    Base,
    Docstring,
    Inline,
    Item,
    Section,
    Type,
    _rename_section,
    parse_parameter,
    parse_returns,
    split_parameter,
    split_section,
)


def test_update_item():
    a = Item("a", Type("int"), Inline("aaa"))
    b = Item("b", Type("str"), Inline("bbb"))
    with pytest.raises(ValueError):  # noqa: PT011
        a.update(b)


def test_section_delete_item():
    a = Item("a", Type("int"), Inline("aaa"))
    b = Item("b", Type("str"), Inline("bbb"))
    c = Item("c", Type("float"), Inline("ccc"))
    s = Section("Parameters", items=[a, b, c])
    del s["b"]
    assert "b" not in s
    with pytest.raises(KeyError):
        del s["x"]


def test_section_merge():
    a = Section("a")
    b = Section("b")
    with pytest.raises(ValueError):  # noqa: PT011
        a.merge(b)


def test_docstring_copy():
    d = Docstring()
    a = Section("Parameters")
    d.set_section(a)
    assert "Parameters" in d
    assert d["Parameters"] is a
    a = Section("Arguments")
    d.set_section(a, copy=True)
    assert "Arguments" in d
    assert d["Arguments"] is not a


def test_copy():
    x = Base("x", "markdown")
    y = x.copy()
    assert y.name == "x"
    assert y.markdown == "markdown"


def test_rename_section():
    assert _rename_section("Warns") == "Warnings"


doc = {}
doc["google"] = """a

    b

c

Args:
    x (int):  The first
        parameter

        with type.
    y: The second
        parameter

        without type.

Raises:
    ValueError: a
        b
    TypeError: c
        d

Returns:
    int: e

    f
"""

doc["numpy"] = """a

    b

c

Parameters
----------
x : int
    The first
    parameter

    with type.
y
    The second
    parameter

    without type.

Raises
------
ValueError
    a
    b
TypeError
    c
    d

Returns
-------
int
    e

    f
"""


@pytest.mark.parametrize("style", ["google", "numpy"])
def test_split_section(style):
    it = split_section(doc[style])
    section, body, style = next(it)
    assert section == ""
    assert body == "a\n\n    b\n\nc"
    section, body, style = next(it)
    assert section == "Parameters"
    if style == "google":
        assert body.startswith("x (int)")
    else:
        assert body.startswith("x : int")
    assert body.endswith("\n    without type.")
    section, body, style = next(it)
    assert section == "Raises"
    if style == "google":
        assert body.startswith("ValueError: a")
    else:
        assert body.startswith("ValueError\n    a")
    assert body.endswith("\n    d")


@pytest.mark.parametrize("style", ["google", "numpy"])
def test_parse_parameter(style):
    it = split_section(doc[style])
    next(it)
    section, body, style = next(it)
    it = split_parameter(body)
    lines = next(it)
    assert len(lines) == 4 if style == "goole" else 5
    item = parse_parameter(lines, style)
    assert item.name == "x"
    assert item.description.markdown == "The first\nparameter\n\nwith type."
    assert item.type.name == "int"
    lines = next(it)
    assert len(lines) == 4 if style == "goole" else 5
    item = parse_parameter(lines, style)
    assert item.name == "y"
    assert item.description.markdown == "The second\nparameter\n\nwithout type."
    assert item.type.name == ""


@pytest.mark.parametrize("style", ["google", "numpy"])
def test_parse_returns(style):
    it = split_section(doc[style])
    next(it)
    next(it)
    next(it)
    section, body, style = next(it)
    type_, markdown = parse_returns(body, style)
    assert markdown == "e\n\nf"
    assert type_ == "int"
