import pytest


def test_node_object():
    from mkapi.node import Definition, get_node
    from mkapi.objects import Class, get_object

    name = "jinja2.Template"
    obj = get_object(name)
    assert isinstance(obj, Class)
    assert obj.name == "Template"
    assert obj.module == "jinja2.environment"
    assert obj.fullname == "jinja2.environment.Template"

    node = get_node(name)
    assert isinstance(node, Definition)
    assert node.name == "Template"
    assert node.module == "jinja2.environment"

    assert node.node is obj.node


def test_parser_module():
    from mkapi.parsers import Parser

    name = "mkapi.node"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "mkapi.node"
    assert parser.module is None
    assert parser.obj.fullname == "mkapi.node"


def test_parser_class():
    from mkapi.parsers import Parser

    name = "mkapi.node.Module"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Module"
    assert parser.module == "mkapi.node"
    assert parser.obj.fullname == "mkapi.node.Module"


def test_parser_class_alias():
    from mkapi.parsers import Parser

    name = "jinja2.Template"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Template"
    assert parser.module == "jinja2"
    assert parser.obj.fullname == "jinja2.environment.Template"


def test_parser_function():
    from mkapi.parsers import Parser

    name = "mkapi.node.get_node"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "get_node"
    assert parser.module == "mkapi.node"
    assert parser.obj.fullname == "mkapi.node.get_node"


def test_parser_method():
    from mkapi.parsers import Parser

    name = "mkapi.parsers.Parser.create"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Parser.create"
    assert parser.module == "mkapi.parsers"
    assert parser.obj.fullname == "mkapi.parsers.Parser.create"


def test_parser_method_alias():
    from mkapi.parsers import Parser

    name = "jinja2.Template.render"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Template.render"
    assert parser.module == "jinja2"
    assert parser.obj.fullname == "jinja2.environment.Template.render"


# @pytest.mark.parametrize("name", ["a.b", "a.b.*", "a.b.**"])
# def test_split_name_depth(name: str):
#     from mkapi.parsers import _split_name_depth

#     assert _split_name_depth(name) == ("a.b", name.count("*"))


# def test_create_converter_module():
#     from mkapi.parsers import create_converter

#     c = create_converter("mkapi.converters.**")
#     assert c
#     assert c.name == "mkapi.converters"
#     assert not c.module
#     assert c.obj.fullname == "mkapi.converters"
#     assert c.maxdepth == 2


# def test_create_converter_class():
#     from mkapi.parsers import create_converter

#     c = create_converter("mkapi.converters.Converter.*")
#     assert c
#     assert c.name == "Converter"
#     assert c.module == "mkapi.converters"
#     assert c.obj.fullname == "mkapi.converters.Converter"
#     assert c.maxdepth == 1


# def test_create_converter_asname():
#     from mkapi.parsers import create_converter

#     c = create_converter("examples.styles.ExampleClassGoogle")
#     assert c
#     assert c.name == "ExampleClassGoogle"
#     assert c.module == "examples.styles"
#     assert c.obj.fullname == "examples.styles.google.ExampleClass"
#     assert c.maxdepth == 0


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
