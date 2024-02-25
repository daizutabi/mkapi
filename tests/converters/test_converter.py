from mkapi.converters import create_converter


def test_create_converter():
    c = create_converter("mkapi.converters")
    assert c.name is None
    c = create_converter("mkapi.converters.Converter")
    assert c.name == "Converter"


def test_convert_name():
    c = create_converter("mkapi.converters")
    n = c.convert_name()
    assert n["id"] == "mkapi.converters"
    assert n["fullname"] == "mkapi.converters"
    assert n["names"] == ["mkapi", "converters"]
    c = create_converter("mkapi.converters.create_converter")
    n = c.convert_name()
    assert n["id"] == "mkapi.converters.create_converter"
    assert n["fullname"] == "mkapi.converters.create\\_converter"
