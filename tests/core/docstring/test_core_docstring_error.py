def test_docstring_error(node):
    doc = node.members[4].docstring
    sections = doc.sections
    assert len(sections) == 4

    section = sections[0]
    assert section.name == ""
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Exceptions are")
    assert item.markdown.endswith("\ndocstring.")

    section = sections[1]
    assert section.name == "Warnings"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Do not")
    assert item.markdown.endswith("section.")

    section = sections[2]
    assert section.name == "Parameters"
    assert len(section.items) == 2

    item = section.items[0]
    assert item.name == "msg"
    assert item.type == "str"
    assert item.markdown.startswith("Human")
    assert item.markdown.endswith("exception.")

    item = section.items[1]
    assert item.name == "code"
    assert item.type == "int, optional"
    assert item.markdown.startswith("Error")
    assert item.markdown.endswith("code.")

    section = sections[3]
    assert section.name == "Attributes"
    assert len(section.items) == 2

    item = section.items[0]
    assert item.name == "msg"
    assert item.type == "str"
    assert item.markdown.startswith("Human")
    assert item.markdown.endswith("exception.")

    item = section.items[1]
    assert item.name == "code"
    assert item.type == "int"
    assert item.markdown.startswith("Exception")
    assert item.markdown.endswith("code.")
