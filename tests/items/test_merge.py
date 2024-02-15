import ast
import inspect

from mkapi.docstrings import parse
from mkapi.items import (
    Parameters,
    Raises,
    Returns,
    iter_parameters,
    iter_raises,
    iter_returns,
    merge_parameters,
    merge_raises,
    merge_returns,
)
from mkapi.utils import get_by_name, get_by_type


def _merge_parameters(node):
    assert isinstance(node, ast.FunctionDef)
    doc = parse(ast.get_docstring(node))
    parameters = list(iter_parameters(node))
    merge_parameters(doc.sections, parameters)
    section = get_by_type(doc.sections, Parameters)
    assert section
    return section.items


def test_merge_parameters_type_annotations(get):
    node = get("function_with_pep484_type_annotations")
    items = _merge_parameters(node)
    for n, t in [("param1", "int"), ("param2", "str")]:
        x = get_by_name(items, n)
        assert x
        assert x.type.expr
        assert ast.unparse(x.type.expr) == t


def test_merge_parameters_default(get):
    node = get("module_level_function")
    items = _merge_parameters(node)
    x = get_by_name(items, "param2")
    assert x
    assert x.default.expr
    assert ast.unparse(x.default.expr) == "None"


def _merge_returns(node):
    assert isinstance(node, ast.FunctionDef)
    doc = parse(ast.get_docstring(node))
    returns = list(iter_returns(node))
    merge_returns(doc.sections, returns)
    section = get_by_type(doc.sections, Returns)
    assert section
    return section.items


def test_merge_returns_type_annotations(get):
    node = get("function_with_pep484_type_annotations")
    items = _merge_returns(node)
    assert items[0].type.expr
    assert ast.unparse(items[0].type.expr) == "bool"


def _merge_raises(node):
    assert isinstance(node, ast.FunctionDef)
    doc = parse(ast.get_docstring(node))
    raises = list(iter_raises(node))
    merge_raises(doc.sections, raises)
    section = get_by_type(doc.sections, Raises)
    assert section
    return section.items


def test_merge_raises():
    src = """
    def f():
        raise ValueError("a")
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    items = _merge_raises(node)
    assert items[0].type.expr
    assert ast.unparse(items[0].type.expr) == "ValueError"
