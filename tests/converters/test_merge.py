import ast
import inspect

from mkapi.converters import merge_attributes, merge_parameters, merge_raises, merge_returns
from mkapi.docs import Section, create_doc
from mkapi.objects import Attribute, Function, create_module
from mkapi.utils import get_by_name


def _get_func_type_annotations():
    module = create_module("examples.styles.google")
    assert module
    func = module.get("function_with_pep484_type_annotations")
    assert isinstance(func, Function)
    return func


def test_merge_parameters_type_annotations():
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
    func = _get_func_type_annotations()
    merge_returns(func.doc.sections, func.node.returns)
    section = get_by_name(func.doc.sections, "Returns")
    assert section
    items = section.items
    assert isinstance(items[0].type, ast.expr)
    assert ast.unparse(items[0].type) == "bool"


def test_merge_raises():
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
    module = create_module("examples.styles.google")
    assert module
    attrs = [x for _, x in module.objects(Attribute)]
    sections = module.doc.sections
    merge_attributes(sections, attrs)
    section = get_by_name(sections, "Attributes")
    assert isinstance(section, Section)
    items = section.items
    assert len(items) == 2
