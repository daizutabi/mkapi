import ast

from mkapi.objects import get_module


def test_():
    module = get_module("mkapi.plugins")
    assert module
    # source = module.source
    # print(source)
    # cls = module.get("MkAPIConfig")
    # print(cls._node.lineno)
    # print(cls._node.end_lineno)
    # print(cls._node.__dict__)
    # print(cls.__module_name__)
    # lines = source.split("\n")
    # print("v" * 10)
    # print("\n".join(lines[cls._node.lineno - 1 : cls._node.end_lineno - 1]))
    # print("^" * 10)
    # cls = module.get("MkAPIConfig")
    # print(cls)
    # x = module.get("Config")
    # print(x)
    # m = get_module_from_import(x)
    # print(m)
    # print(m.get("Config"))
    # print(m.get("Config").unparse())

    # print(ast.unparse(cls._node))
    # print(cls.attributes[0].default)
    # g = module.get("config_options")
    # assert g
    # print(g)
    # m = get_module_from_import(g)
    # assert m
    # print(m)
    # print(cls.bases)
    # print(cls._node.bases)
    # assert 0
