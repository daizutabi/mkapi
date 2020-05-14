def test_docstring_function_with_types_in_docstring(node):
    doc = node.members[5].docstring
    sections = doc.sections
    assert len(sections) == 4

    section = sections[0]
    assert section.name == "default"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("The summary")
    assert item.markdown.endswith("getter method.")

    section = sections[1]
    assert section.name == "attributes"
    assert len(section.items) == 2

    section = sections[2]
    assert section.name == "note"
    assert len(section.items) == 1

    section = sections[3]
    assert section.name == "args"
    assert len(section.items) == 3

    item = section.items[1]
    assert item.name == "param2"
    assert item.type == "int, optional"
    assert item.markdown.startswith("Description")
    assert item.markdown.endswith(" supported.")


def test_docstring_property(node):
    doc = node.members[5].members[1].docstring
    sections = doc.sections
    assert len(sections) == 1

    section = sections[0]
    assert section.name == "default"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "str"
    assert item.markdown.startswith("Properties")
    assert item.markdown.endswith(" method.")

    doc = node.members[5].members[2].docstring
    sections = doc.sections
    assert len(sections) == 1

    section = sections[0]
    assert section.name == "default"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "list of str"
    assert item.markdown.startswith("Properties")
    assert item.markdown.endswith(" here.")

    doc = node.members[5].members[3].docstring
    sections = doc.sections
    assert len(sections) == 4

    section = sections[2]
    assert section.name == "args"
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

    section = sections[3]
    assert section.name == "returns"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "bool"
    assert item.markdown.startswith("True")
    assert item.markdown.endswith("otherwise.")
