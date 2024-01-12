import ast

import mkapi.ast
from mkapi.objects import Module, Object, Parameter, Type, load_module


def set_markdown(obj: Type, module: Module) -> None:
    def callback(name: str) -> str:
        fullname = module.get_fullname(name)
        if fullname:
            return f"[{name}][__mkapi__.{fullname}]"
        return name

    obj.markdown = mkapi.ast.unparse(obj.expr, callback)


def test_expr_mkapi_objects():
    module = load_module("mkapi.objects")
    assert module

    def callback(x: str) -> str:
        fullname = module.get_fullname(x)
        if fullname:
            return f"[{x}][__mkapi__.{fullname}]"
        return x

    cls = module.get_class("Class")
    assert cls
    for p in cls.parameters:
        t = mkapi.ast.unparse(p.type.expr, callback) if p.type else "---"
        print(p.name, t)
    # assert 0
