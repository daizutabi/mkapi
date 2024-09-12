import ast


def _get_func_type_annotations():
    from mkapi.object import Function, create_module

    module = create_module("examples.styles.google")
    assert module
    func = module.get("function_with_pep484_type_annotations")
    assert isinstance(func, Function)
    return func


def test_merge_parameters_type_annotations():
    from mkapi.parser import merge_parameters
    from mkapi.utils import find_item_by_name

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
    from mkapi.utils import find_item_by_name

    func = _get_func_type_annotations()
    merge_returns(func.doc.sections, func.node.returns)
    section = find_item_by_name(func.doc.sections, "Returns")
    assert section
    items = section.items
    assert isinstance(items[0].type, ast.expr)
    assert ast.unparse(items[0].type) == "bool"


def test_merge_raises():
    from mkapi.doc import Section
    from mkapi.parser import merge_raises
    from mkapi.utils import find_item_by_name

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
    from mkapi.doc import Item, Section
    from mkapi.parser import merge_raises
    from mkapi.utils import find_item_by_name

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
    from mkapi.doc import Section
    from mkapi.object import Type, create_module
    from mkapi.parser import merge_attributes
    from mkapi.utils import find_item_by_name

    module = create_module("examples.styles.google")
    assert module
    attrs = [x for _, x in module.get_children(Type)]
    sections = module.doc.sections
    merge_attributes(sections, attrs)
    section = find_item_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 2


def test_merge_attribute_class():
    from mkapi.doc import Section
    from mkapi.object import Class, Type, create_module
    from mkapi.parser import merge_attributes
    from mkapi.utils import find_item_by_name

    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
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
