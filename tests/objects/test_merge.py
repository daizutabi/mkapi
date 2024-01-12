import ast

import pytest

from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Module,
    Parameter,
    load_module,
    modules,
)
from mkapi.utils import get_by_name


def test_split_attribute_docstring(google):
    name = "module_level_variable2"
    node = google.get_member(name)
    assert isinstance(node, Attribute)
    assert node.text
    text = node.text.str
    assert isinstance(text, str)
    assert text.startswith("Module level")
    assert text.endswith("by a colon.")
    assert node.type
    assert isinstance(node.type.expr, ast.Name)
    assert node.type.expr.id == "int"


def test_move_property_to_attributes(google):
    cls = google.get_member("ExampleClass")
    attr = cls.get_attribute("readonly_property")
    assert isinstance(attr, Attribute)
    assert attr.text
    assert attr.text.str.startswith("Properties should be")
    assert attr.type
    assert ast.unparse(attr.type.expr) == "str"
    attr = cls.get_attribute("readwrite_property")
    assert isinstance(attr, Attribute)
    assert attr.text
    assert attr.text.str.endswith("mentioned here.")
    assert attr.type
    assert ast.unparse(attr.type.expr) == "list[str]"


@pytest.fixture()
def module():
    name = "examples.styles.example_google"
    if name in modules:
        del modules[name]
    return load_module(name)


def test_merge_module_attrs(module: Module):
    x = module.get_attribute("module_level_variable1")
    assert isinstance(x, Attribute)
    assert x.text
    assert x.text.str.startswith("Module level")
    assert x.type
    assert isinstance(x.type.expr, ast.Name)
    assert isinstance(x.default, ast.Constant)


def test_merge_function_args(module: Module):
    f = module.get_function("function_with_types_in_docstring")
    assert isinstance(f, Function)
    assert f.text
    p = get_by_name(f.parameters, "param1")
    assert isinstance(p, Parameter)
    assert p.type
    assert isinstance(p.type.expr, ast.Name)
    assert p.text
    assert isinstance(p.text.str, str)
    assert p.text.str.startswith("The first")


def test_merge_function_returns(module: Module):
    f = module.get_function("function_with_types_in_docstring")
    assert isinstance(f, Function)
    r = f.returns
    assert r.name == "Returns"
    assert r.type
    assert isinstance(r.type.expr, ast.Name)
    assert ast.unparse(r.type.expr) == "bool"
    assert r.text
    assert isinstance(r.text.str, str)
    assert r.text.str.startswith("The return")


def test_merge_function_pep484(module: Module):
    f = module.get_function("function_with_pep484_type_annotations")
    assert f
    x = f.get_parameter("param1")
    assert x
    assert x.text
    assert x.text.str.startswith("The first")


def test_merge_generator(module: Module):
    g = module.get_function("example_generator")
    assert g
    assert g.returns.name == "Yields"


def test_postprocess_class(module: Module):
    c = module.get_class("ExampleError")
    assert isinstance(c, Class)
    assert len(c.parameters) == 3  # with `self` at this state.
    assert not c.functions
    c = module.get_class("ExampleClass")
    assert isinstance(c, Class)
    assert len(c.parameters) == 4  # with `self` at this state.
    assert c.parameters[3].type
    assert ast.unparse(c.parameters[3].type.expr) == "list[str]"
    assert c.attributes[0].name == "attr1"
    f = c.get_function("example_method")
    assert f
    assert len(f.parameters) == 3  # with `self` at this state.


def test_postprocess_class_pep526(module: Module):
    c = module.get_class("ExamplePEP526Class")
    assert isinstance(c, Class)
    assert len(c.parameters) == 0
    assert c.text
    assert not c.functions
    assert c.attributes
    assert c.attributes[0].name == "attr1"
    assert c.attributes[0].type
    assert isinstance(c.attributes[0].type.expr, ast.Name)
    assert c.attributes[0].text
    assert c.attributes[0].text.str == "Description of `attr1`."
