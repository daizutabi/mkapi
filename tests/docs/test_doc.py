import ast
import inspect

import pytest

from mkapi.docs import is_empty, iter_merge_sections, iter_merged_items, merge_sections, parse
from mkapi.objects import Function, _create_module
from mkapi.utils import get_by_name


def test_parse():
    doc = parse("")
    assert not doc.type
    assert not doc.text
    assert not doc.sections
    doc = parse("a:\n    b\n")
    assert not doc.type
    assert not doc.text
    assert doc.sections


def test_merge_sections():
    doc = parse("a:\n    x\n\na:\n    y\n\nb:\n    z\n")
    s = doc.sections
    x = merge_sections(s[0], s[1])
    assert x.text == "x\n\ny"
    with pytest.raises(ValueError):  # noqa: PT011
        merge_sections(s[0], s[2])


def test_iter_merge_sections():
    doc = parse("a:\n    x\n\nb:\n    y\n\na:\n    z\n")
    s = doc.sections
    x = list(iter_merge_sections(s[0:2], [s[2]]))
    assert len(x) == 2


def test_is_empty():
    doc = parse("")
    assert is_empty(doc)
    doc = parse("a")
    assert not is_empty(doc)
    doc = parse("a:\n    b\n")
    assert not is_empty(doc)
    doc = parse("Args:\n    b: c\n")
    assert not is_empty(doc)
    doc = parse("Args:\n    b\n")
    assert is_empty(doc)
    doc.sections[0].items[0].text = ""
    assert is_empty(doc)
