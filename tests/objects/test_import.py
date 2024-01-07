import ast
from importlib.util import find_spec

from mkapi.objects import _get_module_from_node, get_module, get_object


def test_import():
    module = get_module("mkapi.plugins")
    assert module
    for x in module.imports:
        obj = get_object(x.fullname)
        print(x.name, x.fullname, obj)
