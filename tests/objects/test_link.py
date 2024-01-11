import ast

import mkapi.ast
from mkapi.objects import Module, Object, Parameter, load_module

# def convert(obj:Object):
#     mkapi.ast._iter_identifiers


#         expr:ast.expr|ast.type_param):
#     if not module :=


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
        t = mkapi.ast.unparse(p.type, callback) if p.type else "---"
        print(p.name, t)
    assert 0
