import ast
import inspect

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.importlib import load_module
from mkapi.items import iter_assigns
from mkapi.objects import (
    Class,
    Function,
    Module,
    create_attribute,
    create_class,
    create_function,
    create_module,
    iter_objects,
    objects,
)
from mkapi.utils import get_by_name, get_module_node


# def test_create_module(google):
#     module = create_module("google", google)
#     assert module.name.str == "google"
#     assert len(module.functions) == 4
#     assert len(module.classes) == 3
#     cls = get_by_name(module.classes, "ExampleClass")
#     assert isinstance(cls, Class)
#     assert cls.fullname.str == "google.ExampleClass"
#     func = get_by_name(cls.functions, "example_method")
#     assert isinstance(func, Function)
#     assert func.fullname.str == "google.ExampleClass.example_method"
#     assert repr(module) == "Module('google')"
#     assert len(module.attributes) == 2
