import ast

import pytest

from mkapi.objects import Module, Parameter, Return, get_module


@pytest.fixture()
def module():
    module = get_module("mkapi.objects")
    assert module
    return module


def test_iter(module: Module):
    names = [o.name for o in module]
    assert "Style" in names
    assert "CACHE_MODULE" in names
    assert "Class" in names
    assert "get_object" in names


def test_empty(module: Module):
    obj = module.get("Style")
    assert obj
    assert list(obj) == []


def test_func(module: Module):
    func = module.get("_get_callable_args")
    assert func
    objs = list(func)
    assert isinstance(objs[0], Parameter)
    assert isinstance(objs[1], Return)


def test_iter_exprs(module: Module):
    func = module.get("_get_module_from_node")
    assert func
    exprs = list(func.iter_exprs())
    assert len(exprs) == 2
    assert ast.unparse(exprs[0]) == "ast.Module"
    assert ast.unparse(exprs[1]) == "Module"
