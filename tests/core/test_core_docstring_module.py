def test_docstring_module(node):
    doc = node.docstring
    sections = doc.sections
    assert len(sections) == 5

    section = sections[0]
    assert section.name == "default"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Example")
    assert item.markdown.endswith(" text.")

    section = sections[1]
    assert section.name == "example"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Examples can")
    assert item.markdown.endswith(".py")

    section = sections[2]
    assert section.name == "default"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("Section breaks")
    assert item.markdown.endswith("starts.")

    section = sections[3]
    assert section.name == "attributes"
    assert len(section.items) == 2

    item = section.items[0]
    assert item.name == "module_level_variable1"
    assert item.type == "int"
    assert item.markdown.startswith("Module level")
    assert item.markdown.endswith("it.")

    item = section.items[1]
    assert item.name == "module_level_variable2"
    assert item.type == "int"
    assert item.markdown.startswith("Module level")
    assert item.markdown.endswith("it. ABC.")

    section = sections[4]
    assert section.name == "todo"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("* For")
    assert item.markdown.endswith("extension")
