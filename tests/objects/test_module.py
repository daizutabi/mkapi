from mkapi.objects import Class, Function, _create_module
from mkapi.utils import get_by_name


def test_create_module(google):
    module = _create_module("google", google)
    assert module.name.str == "google"
    assert len(module.functions) == 4
    assert len(module.classes) == 3
    cls = get_by_name(module.classes, "ExampleClass")
    assert isinstance(cls, Class)
    assert cls.fullname.str == "google.ExampleClass"
    func = get_by_name(cls.functions, "example_method")
    assert isinstance(func, Function)
    assert func.fullname.str == "google.ExampleClass.example_method"
    assert repr(module) == "Module('google')"
    assert len(module.attributes) == 2