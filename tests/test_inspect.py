import ast
import dataclasses

from mkapi.inspect import get_decorator, is_classmethod, is_dataclass, is_staticmethod, iter_decorator_names
from mkapi.objects import Class, Member, create_module
from mkapi.utils import get_by_name, get_module_node


def test_iter_decorator_names():
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src)
    module = create_module("a", node)
    f = module.functions[0]
    assert list(iter_decorator_names(f)) == ["a", "b.c", "d"]


def test_get_decorator():
    name = "mkapi.objects"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    cls = get_by_name(module.classes, "Member")
    assert isinstance(cls, Class)
    assert get_decorator(cls, "dataclasses.dataclass")
    assert is_dataclass(cls)
    assert dataclasses.is_dataclass(Member)
    src = "@a(x)\n@b.c(y)\n@d\ndef f():\n pass"
    node = ast.parse(src)
    module = create_module("a", node)
    f = module.functions[0]
    assert get_decorator(f, "d")
    assert not get_decorator(f, "x")


def test_is_method():
    src = "class A:\n @classmethod\n def f(cls): pass"
    node = ast.parse(src)
    module = create_module("a", node)
    cls = module.classes[0]
    assert isinstance(cls, Class)
    assert is_classmethod(cls.functions[0])
    src = "class A:\n @staticmethod\n def f(cls): pass"
    node = ast.parse(src)
    module = create_module("a", node)
    cls = module.classes[0]
    assert isinstance(cls, Class)
    assert is_staticmethod(cls.functions[0])
