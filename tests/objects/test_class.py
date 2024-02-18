import ast
import inspect

from mkapi.objects import Class, create_class
from mkapi.utils import get_by_name


def test_create_class_nested():
    src = """
    class A:
        class B:
            class C:
                pass
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node)
    assert len(cls.classes) == 1
    assert len(cls.classes[0].classes) == 1


def test_create_class(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node)
    assert isinstance(cls, Class)
    assert cls.name.str == "ExampleClass"
    assert len(cls.parameters) == 4
    assert len(cls.raises) == 0
    assert len(cls.functions) == 5
    assert not get_by_name(cls.functions, "__init__")
    assert get_by_name(cls.functions, "example_method")
    assert get_by_name(cls.functions, "__special__")
    assert get_by_name(cls.functions, "__special_without_docstring__")
    assert get_by_name(cls.functions, "_private")
    assert get_by_name(cls.functions, "_private_without_docstring")
    assert len(cls.attributes) == 7
    section = get_by_name(cls.doc.sections, "Attributes")
    assert section
    for x in [section.items, cls.attributes]:
        assert get_by_name(x, "readonly_property")
        assert get_by_name(x, "readwrite_property")
        for k in [1, 2, 5]:
            assert get_by_name(section.items, f"attr{k}")
    assert repr(cls) == "Class('ExampleClass')"
