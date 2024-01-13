import ast

from mkapi.docstrings import Item, Text, Type, iter_merged_items, merge, parse


def test_iter_merged_items():
    a = [
        Item("a", Type(None), Text("item a")),
        Item("b", Type(ast.Constant("int")), Text("item b")),
    ]
    b = [
        Item("a", Type(ast.Constant("str")), Text("item A")),
        Item("c", Type(ast.Constant("list")), Text("item c")),
    ]
    c = list(iter_merged_items(a, b))
    assert c[0].name == "a"
    assert c[0].type.expr.value == "str"  # type: ignore
    assert c[0].text.str == "item a"
    assert c[1].name == "b"
    assert c[1].type.expr.value == "int"  # type: ignore
    assert c[2].name == "c"
    assert c[2].type.expr.value == "list"  # type: ignore


def test_merge(google, get, get_node):
    a = parse(get(google, "ExampleClass"))
    b = parse(get(get_node(google, "ExampleClass"), "__init__"))
    doc = merge(a, b)
    assert doc
    assert [s.name for s in doc] == ["", "Attributes", "Note", "Parameters", ""]
    doc.sections[-1].text.str.endswith("with it.")  # type: ignore
