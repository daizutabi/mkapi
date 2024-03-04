import pytest


@pytest.mark.parametrize("name", ["a.b", "a.b.*", "a.b.**"])
def test_split_name_depth(name: str):
    from mkapi.converters import _split_name_depth

    assert _split_name_depth(name) == ("a.b", name.count("*"))


def test_create_converter_module():
    from mkapi.converters import create_converter

    c = create_converter("mkapi.converters.**")
    assert c
    assert c.name == "mkapi.converters"
    assert not c.module
    assert c.obj.fullname == "mkapi.converters"
    assert c.maxdepth == 2


def test_create_converter_class():
    from mkapi.converters import create_converter

    c = create_converter("mkapi.converters.Converter.*")
    assert c
    assert c.name == "Converter"
    assert c.module == "mkapi.converters"
    assert c.obj.fullname == "mkapi.converters.Converter"
    assert c.maxdepth == 1


def test_create_converter_asname():
    from mkapi.converters import create_converter

    c = create_converter("examples.styles.ExampleClassGoogle")
    assert c
    assert c.name == "ExampleClassGoogle"
    assert c.module == "examples.styles"
    assert c.obj.fullname == "examples.styles.google.ExampleClass"
    assert c.maxdepth == 0


# def test_():
#     c = create_converter("mkapi.converters")
#     assert c
#     n = c.convert_name()
#     print(n)
#     assert 0
#     assert n["id"] == "mkapi.converters"
#     assert n["fullname"] == "mkapi.converters"
#     assert n["names"] == ["mkapi", "converters"]
#     c = create_converter("mkapi.converters.create_converter")
#     n = c.convert_name()
#     assert n["id"] == "mkapi.converters.create_converter"
#     assert n["fullname"] == "mkapi.converters.create\\_converter"
