# from mkapi.docstrings import merge, parse


# def test_merge(google, get, get_node):
#     a = parse(get(google, "ExampleClass"))
#     b = parse(get(get_node(google, "ExampleClass"), "__init__"))
#     doc = merge(a, b)
#     assert doc
#     names = ["", "Attributes", "Note", "Parameters", ""]
#     assert [s.name for s in doc.sections] == names
#     doc.sections[-1].text.str.endswith("with it.")  # type: ignore
