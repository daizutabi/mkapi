import ast

from astdoc.doc import Item, Section
from astdoc.object import Class, Function, Type, create_module, get_object
from astdoc.utils import find_item_by_name


def _get_func_type_annotations():
    module = create_module("examples._styles.google")
    assert module
    func = module.get("function_with_pep484_type_annotations")
    assert isinstance(func, Function)
    return func


def test_merge_parameters_type_annotations():
    from mkapi.parser import merge_parameters

    func = _get_func_type_annotations()
    merge_parameters(func.doc.sections, func.parameters)
    section = find_item_by_name(func.doc.sections, "Parameters")
    assert section
    items = section.items
    for n, t in [("param1", "int"), ("param2", "str")]:
        x = find_item_by_name(items, n)
        assert x
        assert isinstance(x.type, ast.expr)
        assert ast.unparse(x.type) == t


def test_merge_returns_type_annotations():
    from mkapi.parser import merge_returns

    func = _get_func_type_annotations()
    merge_returns(func.doc.sections, func.node.returns, "dummy")
    section = find_item_by_name(func.doc.sections, "Returns")
    assert section
    items = section.items
    assert isinstance(items[0].type, ast.expr)
    assert ast.unparse(items[0].type) == "bool"


def test_merge_raises():
    from mkapi.parser import merge_raises

    sections = []
    expr = ast.parse("ValueError").body[0]
    assert isinstance(expr, ast.Expr)
    merge_raises(sections, [expr.value])
    section = find_item_by_name(sections, "Raises")
    assert isinstance(section, Section)
    items = section.items
    assert isinstance(items[0].type, ast.expr)
    assert ast.unparse(items[0].type) == "ValueError"


def test_merge_raises_duplicate():
    from mkapi.parser import merge_raises

    sections = [Section("Raises", None, "", [Item("ValueError", None, "")])]
    expr = ast.parse("ValueError").body[0]
    assert isinstance(expr, ast.Expr)
    merge_raises(sections, [expr.value])
    section = find_item_by_name(sections, "Raises")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 1
    assert items[0].name == "ValueError"
    assert not items[0].type


def test_merge_attribute_module():
    from mkapi.parser import merge_attributes

    module = create_module("examples._styles.google")
    assert module
    attrs = [x for _, x in module.get_children(Type)]
    sections = module.doc.sections
    merge_attributes(sections, attrs)
    section = find_item_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 2


def test_merge_attribute_class():
    from mkapi.parser import merge_attributes

    cls = get_object("examples._styles.google.ExampleClass")
    assert isinstance(cls, Class)
    attrs = [x for _, x in cls.get_children(Type)]
    assert len(attrs) == 7
    sections = cls.doc.sections
    merge_attributes(sections, attrs)
    section = find_item_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 7
    item = find_item_by_name(items, "attr5")
    assert item
    assert item.type == "str"
    item = find_item_by_name(items, "readwrite_property")
    assert item
    assert item.type == "list(str)"


def test_merge_attribute_enum():
    from mkapi.parser import merge_attributes

    cls = get_object("inspect._ParameterKind")
    assert isinstance(cls, Class)
    attrs = [x for _, x in cls.get_children(Type)]
    assert len(attrs) >= 5
    sections = cls.doc.sections
    names = ["name", "value"]
    merge_attributes(sections, attrs, ignore_names=names, ignore_empty=False)
    section = find_item_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) >= 5


def test_merge_attribute_private():
    from mkapi.parser import merge_attributes

    cls = get_object("examples.parser.PrivateAttribute")
    assert isinstance(cls, Class)
    attrs = [x for _, x in cls.get_children(Type)]
    assert len(attrs) == 2
    assert attrs[0].name == "x"
    assert attrs[1].name == "_y"
    sections = cls.doc.sections
    merge_attributes(sections, attrs)
    section = find_item_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 1
    assert items[0].name == "x"


def test_merge_attribute_docstring():
    from mkapi.parser import merge_attributes

    cls = get_object("examples.parser.DocstringAttribute")
    assert isinstance(cls, Class)
    attrs = [x for _, x in cls.get_children(Type)]
    assert len(attrs) == 3
    assert attrs[0].name == "x"
    assert attrs[1].name == "y"
    assert attrs[2].name == "z"
    assert attrs[2].doc.text == "attribute z\n\nsecond paragraph"
    sections = cls.doc.sections
    doc_section = find_item_by_name(sections, "Attributes")
    assert doc_section
    assert len(doc_section.items) == 2
    merge_attributes(sections, attrs)
    section = find_item_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    assert doc_section is section
    items = section.items
    assert len(items) == 3
    assert items[0].name == "x"
    assert items[0].type == "integer"
    assert items[0].text == "attribute X"
    assert items[1].name == "y"
    assert isinstance(items[2].type, ast.expr)
    assert ast.unparse(items[2].type) == "int"
    assert items[1].text == "attribute Y"
    assert items[2].name == "z"
    assert isinstance(items[2].type, ast.expr)
    assert ast.unparse(items[2].type) == "int"
    assert items[2].text == "attribute z"


def test_merge_attribute_empty():
    from mkapi.parser import merge_attributes

    sections = []
    merge_attributes(sections, [])
    assert sections == []
