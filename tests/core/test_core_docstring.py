from mkapi.core.docstring import get_docstring, rename_section


def test_function(add):
    doc = get_docstring(add)
    assert len(doc.sections) == 5
    assert doc.sections[0].name == ""
    assert doc.sections[0].markdown.startswith("Returns $")
    assert doc.sections[1].name == "Parameters"
    assert doc.sections[1].items[0].name == "x"
    assert doc.sections[1].items[0].type.name == "int"
    assert doc.sections[1].items[1].name == "y"
    assert doc.sections[1].items[1].type.name == "int, optional"


def test_rename_section():
    assert rename_section('Warns') == 'Warnings'


def test_attributes():
    from mkapi.core.base import Base
    doc = get_docstring(Base)
    for item in doc['Attributes'].items[:3]:
        assert item.type.name == 'str'
        assert item.description
