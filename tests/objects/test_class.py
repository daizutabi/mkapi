import ast
import inspect

from mkapi.objects import Class, Function, Property, create_class, create_module


def test_create_class_nested():
    src = """
    class A:
        class B:
            class C:
                pass
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert len(cls.dict) == 1
    cls = cls.dict["B"]
    assert isinstance(cls, Class)
    assert len(cls.dict) == 1
    cls = cls.dict["C"]
    assert isinstance(cls, Class)


def test_create_class(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert isinstance(cls, Class)
    assert cls.name == "ExampleClass"
    assert len(cls.raises) == 0
    for x in ["_private"]:
        assert isinstance(cls.get(x), Function)
    for x in ["readonly_property", "readwrite_property"]:
        assert isinstance(cls.get(x), Property)


def test_inherit():
    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    func = cls.get("__repr__")
    assert isinstance(func, Function)
    assert func.qualname == "Object.__repr__"
