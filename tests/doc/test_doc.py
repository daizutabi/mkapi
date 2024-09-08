def test_create_doc():
    from mkapi.doc import create_doc

    doc = create_doc("")
    assert not doc.type
    assert not doc.text
    assert not doc.sections
    doc = create_doc("a:\n    b\n")
    assert not doc.type
    assert not doc.text
    assert doc.sections


def test_merge_sections():
    from mkapi.doc import create_doc, merge_sections

    doc = create_doc("a:\n    x\n\na:\n    y\n\nb:\n    z\n")
    s = doc.sections
    x = merge_sections(s[0], s[1])
    assert x.text == "x\n\ny"


def test_iter_merged_sections():
    from mkapi.doc import create_doc, iter_merged_sections

    doc = create_doc("a:\n    x\n\nb:\n    y\n\na:\n    z\n")
    s = doc.sections
    x = list(iter_merged_sections(s[0:2], [s[2]]))
    assert len(x) == 2


def test_is_empty():
    from mkapi.doc import create_doc, is_empty

    doc = create_doc("")
    assert is_empty(doc)
    doc = create_doc("a")
    assert not is_empty(doc)
    doc = create_doc("a:\n    b\n")
    assert not is_empty(doc)
    doc = create_doc("Args:\n    b: c\n")
    assert not is_empty(doc)
    doc = create_doc("Args:\n    b\n")
    assert is_empty(doc)
    doc.sections[0].items[0].text = ""
    assert is_empty(doc)


def test_iter_items_without_name():
    from mkapi.doc import iter_items_without_name

    text = "int: The return value."
    item = next(iter_items_without_name(text, "google"))
    assert item.name == ""
    assert item.type == "int"
    assert item.text == "The return value."


def test_iter_items_without_name_with_colon():
    from mkapi.doc import iter_items_without_name

    text = "x: int\n The return value."
    item = next(iter_items_without_name(text, "numpy"))
    assert item.name == "x"
    assert item.type == "int"
    assert item.text == "The return value."


def test_iter_sections_invalid():
    from mkapi.doc import iter_sections

    text = "Args:\n \nArgs:\n x (int): A param."
    sections = list(iter_sections(text, "google"))
    assert len(sections) == 1


def test_create_admonition_see_also():
    from mkapi.doc import _create_admonition

    admonition = _create_admonition("See Also", "mkapi")
    assert admonition == '!!! info "See Also"\n    [__mkapi__.mkapi][]'


def test_iter_merged_items():
    from mkapi.doc import Item, iter_merged_items

    item1 = Item(name="param1", type="int", text="The first parameter.")
    item2 = Item(name="param2", type="str", text="The second parameter.")
    item3 = Item(name="param1", type="float", text="Updated first parameter.")

    merged_items = list(iter_merged_items([item1, item2], [item3]))
    assert len(merged_items) == 2
    assert merged_items[0].name == "param1"

    merged_items = list(iter_merged_items([item1], [item2, item3]))
    assert len(merged_items) == 2
    assert merged_items[0].name == "param1"


def test_iter_merged_sections_without_name():
    from mkapi.doc import Section, iter_merged_sections

    s1 = Section("", "", "A", [])
    s2 = Section("", "", "B", [])
    s3 = Section("a", "", "C", [])

    merged_sections = list(iter_merged_sections([s1, s2], [s3]))
    assert len(merged_sections) == 3

    merged_sections = list(iter_merged_sections([s1], [s2, s3]))
    assert len(merged_sections) == 3
