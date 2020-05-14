def test_docstring_function_with_types_in_docstring(node):
    doc = node.members[0].docstring
    sections = doc.sections
    assert len(sections) == 3

    section = sections[0]
    assert section.name == ""
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Example function")
    assert item.markdown.endswith(" docstring:")

    section = sections[1]
    assert section.name == "Parameters"
    assert len(section.items) == 2

    item = section.items[0]
    assert item.name == "param1"
    assert item.type == "int"
    assert item.markdown.startswith("The first")
    assert item.markdown.endswith("parameter.")

    item = section.items[1]
    assert item.name == "param2"
    assert item.type == "str"
    assert item.markdown.startswith("The second")
    assert item.markdown.endswith("parameter.")

    section = sections[2]
    assert section.name == "Returns"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "bool"
    assert item.markdown.startswith("The return")
    assert item.markdown.endswith("otherwise.")


def test_docstring_function_with_pep484_type_annotations(node):
    doc = node.members[1].docstring
    sections = doc.sections
    assert len(sections) == 3

    section = sections[0]
    assert section.name == ""
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Example function")
    assert item.markdown.endswith(" annotations.")

    section = sections[1]
    assert section.name == "Parameters"
    assert len(section.items) == 2

    item = section.items[0]
    assert item.name == "param1"
    assert item.type == "int"
    assert item.markdown.startswith("The first")
    assert item.markdown.endswith("parameter.")

    item = section.items[1]
    assert item.name == "param2"
    assert item.type == "str"
    assert item.markdown.startswith("The second")
    assert item.markdown.endswith("parameter.")

    section = sections[2]
    assert section.name == "Returns"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "bool"
    assert item.markdown.startswith("The return")
    assert item.markdown.endswith("otherwise.")
