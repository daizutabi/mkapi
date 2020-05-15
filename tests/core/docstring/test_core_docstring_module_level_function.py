def test_docstring_module_level_function(node):
    doc = node.members[2].docstring
    sections = doc.sections
    assert len(sections) == 4

    section = sections[0]
    assert section.name == ""
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == ""
    assert item.markdown.startswith("This is an")
    assert item.markdown.endswith(" obvious.")

    section = sections[1]
    assert section.name == "Parameters"
    assert len(section.items) == 4

    item = section.items[0]
    assert item.name == "param1"
    assert item.type == "int"
    assert item.markdown.startswith("The first")
    assert item.markdown.endswith("parameter.")

    item = section.items[1]
    assert item.name == "param2"
    assert item.type == "str, optional"
    assert item.markdown.startswith("The second")
    assert item.markdown.endswith("descriptions.")

    item = section.items[2]
    assert item.name == "*args"
    assert item.type == ""
    assert item.markdown.startswith("Variable")
    assert item.markdown.endswith("list.")

    item = section.items[3]
    assert item.name == "**kwargs"
    assert item.type == ""
    assert item.markdown.startswith("Arbitrary")
    assert item.markdown.endswith("arguments.")

    section = sections[2]
    assert section.name == "Returns"
    assert len(section.items) == 1

    item = section.items[0]
    assert item.name == ""
    assert item.type == "bool"
    assert item.markdown.startswith("True")
    assert item.markdown.endswith("the first line.")

    section = sections[3]
    assert section.name == "Raises"
    assert len(section.items) == 2

    item = section.items[0]
    assert item.name == "AttributeError"
    assert item.type == ""
    assert item.markdown.startswith("The `Raises`")
    assert item.markdown.endswith("interface.")

    item = section.items[1]
    assert item.name == "ValueError"
    assert item.type == ""
    assert item.markdown.startswith("If")
    assert item.markdown.endswith("`param1`.")
