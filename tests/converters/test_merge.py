import ast


def _get_func_type_annotations():
    from mkapi.objects import Function, create_module

    module = create_module("examples.styles.google")
    assert module
    func = module.get("function_with_pep484_type_annotations")
    assert isinstance(func, Function)
    return func


def test_merge_parameters_type_annotations():
    from mkapi.converters import merge_parameters
    from mkapi.utils import get_by_name

    func = _get_func_type_annotations()
    merge_parameters(func.doc.sections, func.parameters)
    section = get_by_name(func.doc.sections, "Parameters")
    assert section
    items = section.items
    for n, t in [("param1", "int"), ("param2", "str")]:
        x = get_by_name(items, n)
        assert x
        assert isinstance(x.type, ast.expr)
        assert ast.unparse(x.type) == t


def test_merge_returns_type_annotations():
    from mkapi.converters import merge_returns
    from mkapi.utils import get_by_name

    func = _get_func_type_annotations()
    merge_returns(func.doc.sections, func.node.returns)
    section = get_by_name(func.doc.sections, "Returns")
    assert section
    items = section.items
    assert isinstance(items[0].type, ast.expr)
    assert ast.unparse(items[0].type) == "bool"


def test_merge_raises():
    from mkapi.converters import merge_raises
    from mkapi.docs import Section
    from mkapi.utils import get_by_name

    sections = []
    expr = ast.parse("ValueError").body[0]
    assert isinstance(expr, ast.Expr)
    merge_raises(sections, [expr.value])
    section = get_by_name(sections, "Raises")
    assert isinstance(section, Section)
    items = section.items
    assert isinstance(items[0].type, ast.expr)
    assert ast.unparse(items[0].type) == "ValueError"


def test_merge_attribute_module():
    from mkapi.converters import merge_attributes
    from mkapi.docs import Section
    from mkapi.objects import Attribute, create_module
    from mkapi.utils import get_by_name

    module = create_module("examples.styles.google")
    assert module
    attrs = [x for _, x in module.get_children(Attribute)]
    sections = module.doc.sections
    merge_attributes(sections, attrs)
    section = get_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 2
