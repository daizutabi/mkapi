import pytest

from mkapi.core.base import Base, Docstring, Item, Section


def test_update_item():
    a = Item("a", "int", "aaa")
    b = Item("b", "str", "bbb")
    with pytest.raises(ValueError):
        a.update(b)


def test_section_delete_item():
    a = Item("a", "int", "aaa")
    b = Item("b", "str", "bbb")
    c = Item("c", "float", "ccc")
    s = Section("Parameters", items=[a, b, c])
    del s["b"]
    assert "b" not in s
    with pytest.raises(KeyError):
        del s["x"]


def test_section_merge():
    a = Section("a")
    b = Section("b")
    with pytest.raises(ValueError):
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
    x = Base("x", 'markdown')
    y = x.copy()
    assert y.name == 'x'
    assert y.markdown == 'markdown'
