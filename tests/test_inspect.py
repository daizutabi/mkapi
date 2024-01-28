import ast

import pytest

from mkapi.inspect import (
    get_decorator,
    get_signature,
    is_classmethod,
    is_dataclass,
    iter_decorator_names,
    iter_signature,
)
from mkapi.objects import Class, Function, create_module
from mkapi.utils import get_by_name, get_module_node


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


def get(src: str) -> Function:
    node = ast.parse(src)
    module = create_module("x", node)
    return module.functions[0]


def test_iter_signature_return():
    obj = get("def f(): pass")
    x = list(iter_signature(obj))
    assert x == [("(", "paren"), (")", "paren")]
    obj = get("def f()->bool: pass")
    obj.returns[0].type.markdown = "bool"
    x = list(iter_signature(obj))
    assert x[:3] == [("(", "paren"), (")", "paren"), (" → ", "arrow")]
    assert x[-1] == ("bool", "return")


def sig(src: str) -> str:
    obj = get(f"def f({src}): pass")
    return "".join(x[0].replace(" ", "") for x in iter_signature(obj))


def test_iter_signature_kind():
    assert sig("x,y,z") == "(x,y,z)"
    assert sig("x,/,y,z") == "(x,/,y,z)"
    assert sig("x,/,*,y,z") == r"(x,/,\*,y,z)"
    assert sig("x,/,y,*,z") == r"(x,/,y,\*,z)"
    assert sig("x,y,z,/") == "(x,y,z,/)"
    assert sig("*,x,y,z") == r"(\*,x,y,z)"
    assert sig("*x,y,**z") == r"(\*x,y,\*\*z)"
    assert sig("x,y,/,**z") == r"(x,y,/,\*\*z)"


def test_markdown():
    name = "mkapi.objects"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    func = get_by_name(module.functions, "create_module")
    assert isinstance(func, Function)
    sig = get_signature(func)
    m = sig.markdown
    assert '<span class="ann">[ast][__mkapi__.ast].Module</span>' in m


@pytest.fixture(scope="module")
def DataFrame() -> Class:  # noqa: N802
    node = get_module_node("polars.dataframe.frame")
    assert node
    module = create_module("polars.dataframe.frame", node)
    assert module
    cls = get_by_name(module.classes, "DataFrame")
    assert isinstance(cls, Class)
    return cls


def test_markdown_polars(DataFrame):  # noqa: N803
    func = get_by_name(DataFrame.functions, "to_pandas")
    assert isinstance(func, Function)
    sig = get_signature(func)
    m = sig.markdown
    assert r'<span class="star">\*</span>' in m
    # func = get_by_name(cls.functions, "write_csv")
    # assert isinstance(func, Function)
    # sig = get_signature(func)
    # m = sig.markdown
    # print(m)
    # assert 0


def test_method(DataFrame):  # noqa: N803
    func = get_by_name(DataFrame.functions, "_from_arrow")
    assert isinstance(func, Function)
    assert "classmethod" in iter_decorator_names(func)
    assert is_classmethod(func)
