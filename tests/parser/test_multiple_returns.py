def test_return_type_tuple():
    from mkapi.parser import Parser

    parser = Parser.create("examples.parser.sum_and_product")
    assert parser
    doc = parser.parse_doc()
    assert doc.sections
    section = doc.sections[1]
    assert section.name == "Returns"
    assert section.items
    item = section.items[0]
    assert item.name == "s"
    assert item.type == "int"
    item = section.items[1]
    assert item.name == "p"
    assert item.type == "int"
