from mkapi.docstrings import Item, iter_merged_items, merge, parse


def test_iter_merged_items():
    a = [Item("a", "", "item a"), Item("b", "int", "item b")]
    b = [Item("a", "str", "item A"), Item("c", "list", "item c")]
    c = list(iter_merged_items(a, b))
    assert c[0].name == "a"
    assert c[0].type == "str"
    assert c[0].text == "item a"
    assert c[1].name == "b"
    assert c[1].type == "int"
    assert c[2].name == "c"
    assert c[2].type == "list"


def test_merge(google, get, get_node):
    a = parse(get(google, "ExampleClass"))
    b = parse(get(get_node(google, "ExampleClass"), "__init__"))
    doc = merge(a, b)
    assert doc
    assert [s.name for s in doc] == ["", "Attributes", "Note", "Parameters", ""]
    doc.sections[-1].text.endswith("with it.")
