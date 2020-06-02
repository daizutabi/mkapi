import pytest

from mkapi.core.docstring import (parse_parameter, parse_raise, parse_returns,
                                  split_parameter, split_section)

doc = {}
doc[
    "google"
] = """a

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

doc[
    "numpy"
] = """a

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
    name, type, markdown = parse_parameter(lines, style)
    assert name == "x"
    assert type == "int"
    assert markdown == "The first\nparameter\n\nwith type."
    lines = next(it)
    assert len(lines) == 4 if style == "goole" else 5
    name, type, markdown = parse_parameter(lines, style)
    assert name == "y"
    assert type == ""
    assert markdown == "The second\nparameter\n\nwithout type."


@pytest.mark.parametrize("style", ["google", "numpy"])
def test_parse_raise(style):
    it = split_section(doc[style])
    next(it)
    next(it)
    section, body, style = next(it)
    it = split_parameter(body)
    lines = next(it)
    assert len(lines) == 2 if style == "goole" else 3
    type, markdown = parse_raise(lines, style)
    assert type == "ValueError"
    assert markdown == "a\nb"
    lines = next(it)
    assert len(lines) == 2 if style == "goole" else 3
    type, markdown = parse_raise(lines, style)
    assert type == "TypeError"
    assert markdown == "c\nd"


@pytest.mark.parametrize("style", ["google", "numpy"])
def test_parse_returns(style):
    it = split_section(doc[style])
    next(it)
    next(it)
    next(it)
    section, body, style = next(it)
    type, markdown = parse_returns(body, style)
    assert type == "int"
    assert markdown == "e\n\nf"
    # lines = next(it)
    # assert len(lines) == 2 if style == "goole" else 3
    # type, markdown = parse_raise(lines, style)
    # assert type == "TypeError"
    # assert markdown == "c\nd"
