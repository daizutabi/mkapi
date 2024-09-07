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
