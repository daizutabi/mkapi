def test_docstring_generator(node):
    doc = node.members[3].docstring
    sections = doc.sections
    assert len(sections) == 4

    section = sections[0]
    assert section.name == ""
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Generator")
    assert item.markdown.endswith(" section.")

    section = sections[1]
    assert section.name == "Parameters"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == "n"
    assert item.type == "int"
    assert item.markdown.startswith("The upper")
    assert item.markdown.endswith("- 1.")

    section = sections[2]
    assert section.name == "Yields"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "int"
    assert item.markdown.startswith("The next")
    assert item.markdown.endswith("- 1.")

    section = sections[3]
    assert section.name == "Examples"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Examples")
    assert item.markdown.endswith("\n[0, 1, 2, 3]")
