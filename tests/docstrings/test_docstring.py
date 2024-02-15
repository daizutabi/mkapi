import ast
import inspect

import pytest

from mkapi.docstrings import is_empty, iter_merge_sections, iter_merged_items, merge_sections, parse
from mkapi.items import Item, Name, Text, Type
from mkapi.objects import create_module
from mkapi.utils import get_by_name


def test_parse():
    doc = parse("")
    assert not doc.type.expr
    assert not doc.text.str
    assert not doc.sections
    doc = parse("a:\n    b\n")
    assert not doc.type.expr
    assert not doc.text.str
    assert doc.sections


def test_iter_merged_items():
    """'''test'''
    def f(x: int=0):
        '''function.

        Args:
            x: parameter.'''
    """
    src = inspect.getdoc(test_iter_merged_items)
    assert src
    node = ast.parse(src)
    module = create_module("x", node)
    func = get_by_name(module.functions, "f")
    assert func
    items_ast = func.parameters
    items_doc = func.doc.sections[0].items
    item = next(iter_merged_items(items_ast, items_doc))
    assert item.name.str == "x"
    assert item.type.expr.id == "int"  # type: ignore
    assert item.default.expr.value == 0  # type: ignore
    assert item.text.str == "parameter."


def test_iter_merged_items_():
    a = [
        Item(Name("a"), Type(), Text("item a")),
        Item(Name("b"), Type(ast.Constant("int")), Text("item b")),
    ]
    b = [
        Item(Name("a"), Type(ast.Constant("str")), Text("item A")),
        Item(Name("c"), Type(ast.Constant("list")), Text("item c")),
    ]
    c = list(iter_merged_items(a, b))
    assert c[0].name.str == "a"
    assert c[0].type.expr.value == "str"  # type: ignore
    assert c[0].text.str == "item a"
    assert c[1].name.str == "b"
    assert c[1].type.expr.value == "int"  # type: ignore
    assert c[2].name.str == "c"
    assert c[2].type.expr.value == "list"  # type: ignore


def test_merge_sections():
    doc = parse("a:\n    x\n\na:\n    y\n\nb:\n    z\n")
    s = doc.sections
    x = merge_sections(s[0], s[1])
    assert x.text.str == "x\n\ny"
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
    doc.sections[0].items[0].text.str = ""
    assert is_empty(doc)
