import pytest


@pytest.mark.parametrize("name", ["a.b", "a.b.*", "a.b.**"])
def test_split_name_depth(name: str):
    from mkapi.converters import _split_name_depth

    assert _split_name_depth(name) == ("a.b", name.count("*"))


@pytest.fixture
def converter_module():
    from mkapi.converters import create_converter

    return create_converter("mkapi.converters.**")


def test_create_converter_module(converter_module):
    c = converter_module
    assert c.name == "mkapi.converters"
    assert not c.module
    assert c.obj.fullname == "mkapi.converters"
    assert c.depth == 2


@pytest.fixture
def converter_class():
    from mkapi.converters import create_converter

    return create_converter("mkapi.converters.Converter.*")


def test_create_converter_class(converter_class):
    c = converter_class
    assert c.name == "Converter"
    assert c.module == "mkapi.converters"
    assert c.obj.fullname == "mkapi.converters.Converter"
    assert c.depth == 1


@pytest.fixture
def converter_asname():
    from mkapi.converters import create_converter

    return create_converter("examples.styles.ExampleClassGoogle")


def test_create_converter_asname(converter_asname):
    c = converter_asname
    assert c.name == "ExampleClassGoogle"
    assert c.module == "examples.styles"
    assert c.obj.fullname == "examples.styles.google.ExampleClass"
    assert c.depth == 0


def test_get_members(converter_module):
    from mkapi.converters import _get_members

    x = list(_get_members(converter_module.obj))
    print(x)
    assert 0


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
