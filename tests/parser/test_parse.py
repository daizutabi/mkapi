import pytest
from astdoc.doc import Doc


def test_node_object():
    from astdoc.node import Definition, get_node
    from astdoc.object import Class, get_object

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

    name = "astdoc.node"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "astdoc.node"
    assert parser.module is None
    assert parser.obj.fullname == "astdoc.node"


def test_parser_class():
    from mkapi.parser import Parser

    name = "astdoc.node.Module"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "Module"
    assert parser.module == "astdoc.node"
    assert parser.obj.fullname == "astdoc.node.Module"


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

    name = "astdoc.node.get_node"
    parser = Parser.create(name)
    assert parser
    assert parser.name == "get_node"
    assert parser.module == "astdoc.node"
    assert parser.obj.fullname == "astdoc.node.get_node"


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


def test_parser_invalid_package():
    from mkapi.parser import Parser

    name = "invalid"
    parser = Parser.create(name)
    assert parser is None


def test_parser_invalid_module():
    from mkapi.parser import Parser

    name = "astdoc.invalid"
    parser = Parser.create(name)
    assert parser is None


def test_parser_repr_module():
    from mkapi.parser import Parser

    name = "astdoc.node"
    parser = Parser.create(name)
    assert repr(parser) == "Parser('astdoc.node', None)"


def test_parser_repr_object():
    from mkapi.parser import Parser

    name = "astdoc.node.Node"
    parser = Parser.create(name)
    assert repr(parser) == "Parser('Node', 'astdoc.node')"


def test_parse_name_set_module():
    from mkapi.parser import Parser

    name = "astdoc.ast"
    parser = Parser.create(name)
    assert parser
    name_set = parser.parse_name_set()
    assert name_set.kind == "module"
    assert name_set.name == "astdoc.ast"
    assert name_set.parent is None
    assert name_set.module is None
    assert name_set.fullname == "astdoc.ast"
    assert name_set.id == "astdoc.ast"
    assert name_set.obj_id == "astdoc.ast"
    assert name_set.parent_id is None


def test_parse_name_set_function():
    from mkapi.parser import Parser

    name = "astdoc.ast.get_assign_name"
    parser = Parser.create(name)
    assert parser
    name_set = parser.parse_name_set()
    assert name_set.kind == ""
    assert name_set.name == "get\\_assign\\_name"
    assert name_set.parent is None
    assert name_set.module == "astdoc.ast"
    assert name_set.fullname == "astdoc.ast.get\\_assign\\_name"
    assert name_set.id == "astdoc.ast.get_assign_name"
    assert name_set.obj_id == "astdoc.ast.get_assign_name"
    assert name_set.parent_id is None


def test_parse_name_set_staticmethod():
    from mkapi.parser import Parser

    name = "mkapi.parser.Parser.create"
    parser = Parser.create(name)
    assert parser
    name_set = parser.parse_name_set()
    assert name_set.kind == "classmethod"
    assert name_set.name == "create"
    assert name_set.parent == "Parser"
    assert name_set.module == "mkapi.parser"
    assert name_set.fullname == "mkapi.parser.Parser.create"
    assert name_set.id == "mkapi.parser.Parser.create"
    assert name_set.obj_id == "mkapi.parser.Parser.create"
    assert name_set.parent_id == "mkapi.parser.Parser"


def test_parse_name_set_export():
    from mkapi.parser import Parser

    name = "jinja2.Template.render"
    parser = Parser.create(name)
    assert parser
    name_set = parser.parse_name_set()
    assert name_set.id == "jinja2.Template.render"
    assert name_set.obj_id == "jinja2.environment.Template.render"
    assert name_set.fullname == "jinja2.Template.render"


def test_parse_name_set_alias():
    from mkapi.parser import Parser

    name = "examples.ExampleClassA"
    parser = Parser.create(name)
    assert parser
    name = parser.parse_name_set()
    assert name.id == "examples.ExampleClassA"
    assert name.obj_id == "examples.a.ExampleClass"
    assert name.fullname == "examples.ExampleClassA"


def test_parse_signature():
    from mkapi.parser import Parser

    name = "astdoc.ast._iter_parameters"
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
    assert signature[6][0].startswith(
        "[Iterator][__mkapi__.collections.abc.Iterator][",
    )
    assert signature[6][1] == "return"


@pytest.fixture
def doc_func():
    from mkapi.parser import Parser

    name = "examples._usage.func"
    parser = Parser.create(name)
    assert parser
    return parser.parse_doc()


def test_parse_doc_function_text(doc_func: Doc):
    expected = "Docstring [`D`][__mkapi__.astdoc.node.Definition]."
    assert doc_func.text.rstrip() == expected


def test_parse_doc_function_args(doc_func: Doc):
    assert doc_func.sections[0].name == "Parameters"
    items = doc_func.sections[0].items
    assert items[0].name == "a"
    assert items[0].type == "[Object][__mkapi__.astdoc.object.Object]"
    assert items[0].text == "A."
    assert items[1].name == "b"
    assert items[1].text.startswith("B [`I`][__mkapi__.astdoc.doc.Item]")
    assert items[1].text.endswith(" [`Object`][__mkapi__.astdoc.object.Object].")


def test_parse_doc_function_returns(doc_func: Doc):
    assert doc_func.sections[1].name == "Returns"
    items = doc_func.sections[1].items
    assert items[0].name == ""
    assert items[0].type == "[I][__mkapi__.astdoc.doc.Item]"
    assert items[0].text == "C."


@pytest.fixture
def doc_class():
    from mkapi.parser import Parser

    name = "examples._usage.A"
    parser = Parser.create(name)
    assert parser
    return parser.parse_doc()


def test_parse_doc_class_text(doc_class: Doc):
    assert doc_class.text == "Docstring [`I`][__mkapi__.astdoc.doc.Item]."


def test_parse_doc_class_attrs(doc_class: Doc):
    assert doc_class.sections[0].name == "Attributes"
    items = doc_class.sections[0].items
    assert items[0].name == "x"
    assert items[0].type == "[D][__mkapi__.astdoc.node.Definition]"
    assert items[0].text == "Attribute [`D`][__mkapi__.astdoc.node.Definition]."


def test_parse_bases():
    from mkapi.parser import Parser

    name = "astdoc.object.Function"
    parser = Parser.create(name)
    assert parser
    bases = parser.parse_bases()
    assert len(bases) == 1
    assert bases[0] == "[Definition][__mkapi__.astdoc.object.Definition]"


def test_parse_bases_empty():
    from mkapi.parser import Parser

    name = "mkapi.parser.Parser"
    parser = Parser.create(name)
    assert parser
    assert parser.parse_bases() == []


def test_parse_signature_empty():
    from mkapi.parser import Parser

    name = "mkapi.parser"
    parser = Parser.create(name)
    assert parser
    assert parser.parse_signature() == []


def test_parsr_doc_summary_modules():
    from mkapi.parser import Parser

    name = "mkapi.parser"
    parser = Parser.create(name)
    assert parser
    doc = parser.parse_doc()
    assert len(doc.sections) == 2
    assert doc.sections[0].name == "Classes"
    assert doc.sections[0].items[0].name == "[NameSet][__mkapi__.mkapi.parser.NameSet]"
    assert doc.sections[1].name == "Functions"
    n = r"[get\_markdown\_link][__mkapi__.mkapi.parser.get_markdown_link]"
    assert doc.sections[1].items[0].name == n


def test_parsr_doc_summary_classes():
    from astdoc.utils import find_item_by_name

    from mkapi.parser import Parser

    name = "mkapi.plugin"
    parser = Parser.create(name)
    assert parser
    doc = parser.parse_doc()
    section = find_item_by_name(doc.sections, "Classes")
    assert section
    x = "[Plugin][__mkapi__.mkapi.plugin.Plugin]"
    assert section.items[0].name == x


def test_parsr_doc_summary_functions():
    from astdoc.utils import find_item_by_name

    from mkapi.parser import Parser

    name = "mkapi.nav"
    parser = Parser.create(name)
    assert parser
    doc = parser.parse_doc()
    section = find_item_by_name(doc.sections, "Functions")
    assert section
    assert len(section.items) == 6


def test_parsr_doc_summary_methods():
    from astdoc.utils import find_item_by_name

    from mkapi.parser import Parser

    name = "mkapi.parser.Parser"
    parser = Parser.create(name)
    assert parser
    doc = parser.parse_doc()
    section = find_item_by_name(doc.sections, "Methods")
    assert section

    assert len(section.items) == 8
    assert section.items[0].name == "[create][__mkapi__.mkapi.parser.Parser.create]"
