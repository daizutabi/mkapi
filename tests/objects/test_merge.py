import ast

import pytest

from mkapi.docstrings import Docstring
from mkapi.objects import (
    CACHE_MODULE,
    Attribute,
    Class,
    Function,
    Module,
    Parameter,
    get_module,
)
from mkapi.utils import get_by_name


def test_split_attribute_docstring(google):
    name = "module_level_variable2"
    node = google.get(name)
    assert isinstance(node, Attribute)
    assert isinstance(node.docstring, str)
    assert node.docstring.startswith("Module level")
    assert node.docstring.endswith("by a colon.")
    assert isinstance(node.type, ast.Name)
    assert node.type.id == "int"


def test_move_property_to_attributes(google):
    cls = google.get("ExampleClass")
    attr = cls.get("readonly_property")
    assert isinstance(attr, Attribute)
    assert attr.docstring
    assert attr.docstring.startswith("Properties should be")
    assert ast.unparse(attr.type) == "str"  # type: ignore
    attr = cls.get("readwrite_property")
    assert isinstance(attr, Attribute)
    assert attr.docstring
    assert attr.docstring.endswith("mentioned here.")
    assert ast.unparse(attr.type) == "list[str]"  # type: ignore


@pytest.fixture()
def module():
    name = "examples.styles.example_google"
    if name in CACHE_MODULE:
        del CACHE_MODULE[name]
    return get_module(name)


def test_merge_module_attrs(module: Module):
    x = module.get_attribute("module_level_variable1")
    assert isinstance(x, Attribute)
    assert x.docstring
    assert x.docstring.startswith("Module level")
    assert isinstance(x.type, ast.Name)
    assert isinstance(x.default, ast.Constant)
    assert isinstance(module.docstring, Docstring)
    assert len(module.docstring.sections) == 5
    assert get_by_name(module.docstring.sections, "Attributes") is None


def test_merge_function_args(module: Module):
    f = module.get_function("function_with_types_in_docstring")
    assert isinstance(f, Function)
    assert isinstance(f.docstring, Docstring)
    assert len(f.docstring.sections) == 2
    p = get_by_name(f.parameters, "param1")
    assert isinstance(p, Parameter)
    assert isinstance(p.type, ast.Name)
    assert isinstance(p.docstring, str)
    assert p.docstring.startswith("The first")


def test_merge_function_returns(module: Module):
    f = module.get_function("function_with_types_in_docstring")
    assert isinstance(f, Function)
    r = f.returns
    assert r.name == "Returns"
    assert isinstance(r.type, ast.Name)
    assert ast.unparse(r.type) == "bool"
    assert isinstance(r.docstring, str)
    assert r.docstring.startswith("The return")


def test_merge_function_pep484(module: Module):
    f = module.get_function("function_with_pep484_type_annotations")
    x = f.get_parameter("param1")  # type: ignore
    assert x.docstring.startswith("The first")  # type: ignore


def test_merge_generator(module: Module):
    g = module.get_function("example_generator")
    assert g.returns.name == "Yields"  # type: ignore


def test_postprocess_class(module: Module):
    c = module.get_class("ExampleError")
    assert isinstance(c, Class)
    assert len(c.parameters) == 3  # with `self` at this state.
    assert len(c.docstring.sections) == 2  # type: ignore
    assert not c.functions
    c = module.get_class("ExampleClass")
    assert isinstance(c, Class)
    assert len(c.parameters) == 4  # with `self` at this state.
    assert len(c.docstring.sections) == 3  # type: ignore
    assert ast.unparse(c.parameters[3].type) == "list[str]"  # type: ignore
    assert c.attributes[0].name == "attr1"
    f = c.get_function("example_method")
    assert f
    assert len(f.parameters) == 3  # with `self` at this state.


def test_postprocess_class_pep526(module: Module):
    c = module.get_class("ExamplePEP526Class")
    assert isinstance(c, Class)
    assert len(c.parameters) == 0
    assert len(c.docstring.sections) == 1  # type: ignore
    assert not c.functions
    assert c.attributes
    assert c.attributes[0].name == "attr1"
    assert isinstance(c.attributes[0].type, ast.Name)
    assert c.attributes[0].docstring == "Description of `attr1`."
