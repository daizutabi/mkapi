import ast
import inspect
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.elements import Return
from mkapi.objects import (
    Class,
    Function,
    create_class,
    create_function,
    create_module,
    iter_elements,
    iter_objects,
    objects,
)
from mkapi.utils import get_by_name, get_module_path


def load_module_node(name):
    path = get_module_path(name)
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


@pytest.fixture(scope="module")
def google():
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    return load_module_node("examples.styles.example_google")


@pytest.fixture(scope="module")
def get(google):
    def get(name, *rest, node=google):
        for child in iter_child_nodes(node):
            if not isinstance(child, ast.FunctionDef | ast.ClassDef):
                continue
            if child.name == name:
                if not rest:
                    return child
                return get(*rest, node=child)
        raise NameError

    return get


def test_create_function(get):
    node = get("module_level_function")
    assert isinstance(node, ast.FunctionDef)
    func = create_function(node)
    assert isinstance(func, Function)
    assert func.name == "module_level_function"
    assert func.qualname == "module_level_function"
    assert func.fullname == "__mkapi__.module_level_function"
    assert "__mkapi__.module_level_function" in objects
    assert objects["__mkapi__.module_level_function"] is func
    assert len(func.parameters) == 4
    assert func.get_parameter("param1")
    assert func.get_parameter("param2")
    assert func.get_parameter("args")
    assert func.get_parameter("kwargs")
    assert len(func.returns) == 0
    assert len(func.raises) == 1
    assert len(func.doc.sections) == 4
    assert repr(func) == "Function(module_level_function)"


def test_create_class(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node)
    assert isinstance(cls, Class)
    assert cls.name == "ExampleClass"
    assert len(cls.parameters) == 0
    assert len(cls.raises) == 0
    assert len(cls.functions) == 6
    assert cls.get_function("__init__")
    assert cls.get_function("example_method")
    assert cls.get_function("__special__")
    assert cls.get_function("__special_without_docstring__")
    assert cls.get_function("_private")
    assert cls.get_function("_private_without_docstring")
    assert len(cls.attributes) == 2
    assert cls.get_attribute("readonly_property")
    assert cls.get_attribute("readwrite_property")
    func = cls.get_function("__init__")
    assert isinstance(func, Function)
    assert func.qualname == "ExampleClass.__init__"
    assert func.fullname == "__mkapi__.ExampleClass.__init__"
    assert repr(cls) == "Class(ExampleClass)"


def test_create_module(google):
    module = create_module(google, "google")
    assert module.name == "google"
    assert len(module.functions) == 4
    assert len(module.classes) == 3
    cls = module.get_class("ExampleClass")
    assert isinstance(cls, Class)
    assert cls.fullname == "google.ExampleClass"
    func = cls.get_function("example_method")
    assert isinstance(func, Function)
    assert func.fullname == "google.ExampleClass.example_method"
    assert repr(module) == "Module(google)"


def test_relative_import():
    """# test module
    from .c import d
    from ..e import f
    """
    src = inspect.getdoc(test_relative_import)
    assert src
    node = ast.parse(src)
    module = create_module(node, "x.y.z")
    i = module.get_import("d")
    assert i
    assert i.fullname == "x.y.z.c.d"
    i = module.get_import("f")
    assert i
    assert i.fullname == "x.y.e.f"


def test_iter():
    """# test module
    m: str
    n = 1
    class A(D):
        a: int
        def f(x: int, y: str) -> bool:
            class B(E):
                c: list
            raise ValueError
    """
    src = inspect.getdoc(test_iter)
    assert src
    node = ast.parse(src)
    module = create_module(node, "x")
    cls = module.get_class("A")
    assert cls
    func = cls.get_function("f")
    assert func
    cls = func.get_class("B")
    assert cls
    assert cls.fullname == "x.A.f.B"

    objs = iter_objects(module)
    assert next(objs).name == "A"
    assert next(objs).name == "f"
    assert next(objs).name == "B"
    elms = list(iter_elements(module))
    for x in "mnaxyc":
        assert get_by_name(elms, x)
    assert get_by_name(elms, "ValueError")
    assert any(isinstance(x, Return) for x in elms)
