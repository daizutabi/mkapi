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
    assert "modules" in names
    assert "Class" in names
    assert "get_object" in names


def test_func(module: Module):
    func = module.get("_callable_args")
    assert func
    objs = list(func)
    assert isinstance(objs[0], Parameter)
    assert isinstance(objs[1], Return)


def test_iter_exprs(module: Module):
    func = module.get("get_module_from_node")
    assert func
    exprs = list(func.iter_exprs())
    assert len(exprs) == 4
    assert ast.unparse(exprs[0]) == "ast.Module"
    assert ast.unparse(exprs[1]) == "str"
    assert ast.unparse(exprs[2]) == "'__mkapi__'"
    assert ast.unparse(exprs[3]) == "Module"


def test_iter_bases(module: Module):
    cls = module.get_class("Class")
    assert cls
    bases = cls.iter_bases()
    assert next(bases).name == "Object"
    assert next(bases).name == "Member"
    assert next(bases).name == "Callable"
    assert next(bases).name == "Class"
