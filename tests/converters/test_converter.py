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
    assert c.depth == 2


def test_create_converter_class():
    from mkapi.converters import create_converter

    c = create_converter("mkapi.converters.Converter.*")
    assert c
    assert c.name == "Converter"
    assert c.module == "mkapi.converters"
    assert c.obj.fullname == "mkapi.converters.Converter"
    assert c.depth == 1


def test_create_converter_asname():
    from mkapi.converters import create_converter

    c = create_converter("examples.styles.ExampleClassGoogle")
    assert c
    assert c.name == "ExampleClassGoogle"
    assert c.module == "examples.styles"
    assert c.obj.fullname == "examples.styles.google.ExampleClass"
    assert c.depth == 0


def test_iter_object_module():
    from mkapi.converters import _iter_object
    from mkapi.objects import Module, get_object

    obj = get_object("examples.styles.google")
    obj = get_object("examples.styles")
    assert isinstance(obj, Module)
    x = list(_iter_object(obj, obj.fullname, 2))
    for a in x:
        print(a)
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
