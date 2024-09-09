import pytest

from mkapi.doc import Doc


def test_node_object():
    from mkapi.node import Definition, get_node
    from mkapi.object import Class, get_object

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
    from mkapi.parser import Parser

    name = "mkapi.node"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "mkapi.node"
    assert parser.module is None
    assert parser.obj.fullname == "mkapi.node"


def test_parser_class():
    from mkapi.parser import Parser

    name = "mkapi.node.Module"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Module"
    assert parser.module == "mkapi.node"
    assert parser.obj.fullname == "mkapi.node.Module"


def test_parser_class_alias():
    from mkapi.parser import Parser

    name = "jinja2.Template"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Template"
    assert parser.module == "jinja2"
    assert parser.obj.fullname == "jinja2.environment.Template"


def test_parser_function():
    from mkapi.parser import Parser

    name = "mkapi.node.get_node"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "get_node"
    assert parser.module == "mkapi.node"
    assert parser.obj.fullname == "mkapi.node.get_node"


def test_parser_method():
    from mkapi.parser import Parser

    name = "mkapi.parser.Parser.create"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Parser.create"
    assert parser.module == "mkapi.parser"
    assert parser.obj.fullname == "mkapi.parser.Parser.create"


def test_parser_method_alias():
    from mkapi.parser import Parser

    name = "jinja2.Template.render"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Template.render"
    assert parser.module == "jinja2"
    assert parser.obj.fullname == "jinja2.environment.Template.render"


def test_parse_name_module():
    from mkapi.parser import Parser

    name = "mkapi.ast"
    parser = Parser.create(name)
    assert parser
    name = parser.parse_name()
    assert name.node.id == "mkapi.ast"
    assert name.obj.id == "mkapi.ast"

    names = name.node.fullname.split("].[")
    assert names[0] == "[mkapi][__mkapi__.mkapi"
    assert names[1] == "ast][__mkapi__.mkapi.ast]"
    assert name.node.names == ["mkapi", "ast"]


def test_parse_name_function():
    from mkapi.parser import Parser

    name = "mkapi.ast.get_assign_name"
    parser = Parser.create(name)
    assert parser
    name = parser.parse_name()
    assert name.node.id == "mkapi.ast.get_assign_name"

    names = name.node.fullname.split("].[")
    assert names[0] == "[mkapi][__mkapi__.mkapi"
    assert names[1] == "ast][__mkapi__.mkapi.ast"
    assert names[2] == "get\\_assign\\_name][__mkapi__.mkapi.ast.get_assign_name]"
    assert name.node.names == ["get\\_assign\\_name"]


def test_parse_name_method():
    from mkapi.parser import Parser

    name = "mkapi.parser.Parser.create"
    parser = Parser.create(name)
    assert parser
    name = parser.parse_name()
    assert name.node.id == "mkapi.parser.Parser.create"

    names = name.node.fullname.split("].[")
    assert names[0] == "[mkapi][__mkapi__.mkapi"
    assert names[1] == "parser][__mkapi__.mkapi.parser"
    assert names[2] == "Parser][__mkapi__.mkapi.parser.Parser"
    assert names[3] == "create][__mkapi__.mkapi.parser.Parser.create]"
    assert name.node.names == ["Parser", "create"]


def test_parse_name_export():
    from mkapi.parser import Parser

    name = "jinja2.Template.render"
    parser = Parser.create(name)
    assert parser
    name = parser.parse_name()
    assert name.node.id == "jinja2.Template.render"
    assert name.obj.id == "jinja2.environment.Template.render"

    names = name.node.fullname.split("].[")
    assert names[0] == "[jinja2][__mkapi__.jinja2"
    assert names[1] == "Template][__mkapi__.jinja2.Template"
    assert names[2] == "render][__mkapi__.jinja2.Template.render]"
    assert name.node.names == ["Template", "render"]

    names = name.obj.fullname.split("].[")
    assert names[0] == "[jinja2][__mkapi__.jinja2"
    assert names[1] == "environment][__mkapi__.jinja2.environment"
    assert names[2] == "Template][__mkapi__.jinja2.environment.Template"
    assert names[3] == "render][__mkapi__.jinja2.environment.Template.render]"
    assert name.node.names == ["Template", "render"]
    assert name.obj.names == ["Template", "render"]


def test_parse_name_alias():
    from mkapi.parser import Parser

    name = "examples.styles.ExampleClassGoogle"
    parser = Parser.create(name)
    assert parser
    name = parser.parse_name()
    assert name.node.id == "examples.styles.ExampleClassGoogle"
    assert name.obj.id == "examples.styles.google.ExampleClass"

    names = name.node.fullname.split("].[")
    assert names[0] == "[examples][__mkapi__.examples"
    assert names[1] == "styles][__mkapi__.examples.styles"
    assert names[2].endswith("Google][__mkapi__.examples.styles.ExampleClassGoogle]")
    assert name.node.names == ["ExampleClassGoogle"]

    names = name.obj.fullname.split("].[")
    assert names[0] == "[examples][__mkapi__.examples"
    assert names[1] == "styles][__mkapi__.examples.styles"
    assert names[2] == "google][__mkapi__.examples.styles.google"
    assert names[3] == "ExampleClass][__mkapi__.examples.styles.google.ExampleClass]"
    assert name.obj.names == ["ExampleClass"]


def test_parse_signature():
    from mkapi.parser import Parser

    name = "mkapi.ast._iter_parameters"
    parser = Parser.create(name)
    assert parser
    signature = parser.parse_signature()
    assert signature[0] == ("(", "paren")
    assert signature[1] == ("node", "arg")
    assert signature[2] == (": ", "colon")
    assert signature[3][0].startswith("[FunctionDef][__mkapi__.ast.FunctionDef] | [")
    assert signature[3][0].endswith("][__mkapi__.ast.AsyncFunctionDef]")
    assert signature[3][1] == "ann"
    assert signature[4] == (")", "paren")
    assert signature[5] == (" → ", "arrow")
    assert signature[6][0].startswith("[Iterator][__mkapi__.collections.abc.Iterator][")
    assert signature[6][1] == "return"


@pytest.fixture
def doc_func():
    from mkapi.parser import Parser

    name = "examples.usage.func"
    parser = Parser.create(name)
    assert parser
    return parser.parse_doc()


def test_parse_doc_function_text(doc_func: Doc):
    assert doc_func.text == "Docstring [`D`][__mkapi__.mkapi.node.Definition]."


def test_parse_doc_function_args(doc_func: Doc):
    assert doc_func.sections[0].name == "Parameters"
    items = doc_func.sections[0].items
    assert items[0].name == "a"
    assert items[0].type == "[Object][__mkapi__.mkapi.object.Object]"
    assert items[0].text == "A."
    assert items[1].name == "b"
    assert items[1].text.startswith("B [`I`][__mkapi__.mkapi.doc.Item]")
    assert items[1].text.endswith(" [`Object`][__mkapi__.mkapi.object.Object].")


def test_parse_doc_function_returns(doc_func: Doc):
    assert doc_func.sections[1].name == "Returns"
    items = doc_func.sections[1].items
    assert items[0].name == ""
    assert items[0].type == "[I][__mkapi__.mkapi.doc.Item]"
    assert items[0].text == "C."


@pytest.fixture
def doc_class():
    from mkapi.parser import Parser

    name = "examples.usage.A"
    parser = Parser.create(name)
    assert parser
    return parser.parse_doc()


def test_parse_doc_class_text(doc_class: Doc):
    assert doc_class.text == "Docstring [`I`][__mkapi__.mkapi.doc.Item]."


def test_parse_doc_class_attrs(doc_class: Doc):
    assert doc_class.sections[0].name == "Attributes"
    items = doc_class.sections[0].items
    assert items[0].name == "x"
    assert items[0].type == "[D][__mkapi__.mkapi.node.Definition]"
    assert items[0].text == "Attribute [`D`][__mkapi__.mkapi.node.Definition]."
