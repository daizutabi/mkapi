import ast
import inspect
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.docstrings import Docstring
from mkapi.items import Attributes, Item, Parameters, Raises, Return, Returns, Section
from mkapi.objects import (
    Class,
    Function,
    create_class,
    create_function,
    create_module,
    iter_items,
    iter_objects,
    merge_items,
    merge_parameters,
    merge_returns,
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
    assert get_by_name(func.parameters, "param1")
    assert get_by_name(func.parameters, "param2")
    assert get_by_name(func.parameters, "args")
    assert get_by_name(func.parameters, "kwargs")
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
    assert get_by_name(cls.functions, "__init__")
    assert get_by_name(cls.functions, "example_method")
    assert get_by_name(cls.functions, "__special__")
    assert get_by_name(cls.functions, "__special_without_docstring__")
    assert get_by_name(cls.functions, "_private")
    assert get_by_name(cls.functions, "_private_without_docstring")
    assert len(cls.attributes) == 2
    assert cls.get_attribute("readonly_property")
    assert cls.get_attribute("readwrite_property")
    func = get_by_name(cls.functions, "__init__")
    assert isinstance(func, Function)
    assert func.qualname == "ExampleClass.__init__"
    assert func.fullname == "__mkapi__.ExampleClass.__init__"
    assert repr(cls) == "Class(ExampleClass)"


def test_create_module(google):
    module = create_module(google, "google")
    assert module.name == "google"
    assert len(module.functions) == 4
    assert len(module.classes) == 3
    cls = get_by_name(module.classes, "ExampleClass")
    assert isinstance(cls, Class)
    assert cls.fullname == "google.ExampleClass"
    func = get_by_name(cls.functions, "example_method")
    assert isinstance(func, Function)
    assert func.fullname == "google.ExampleClass.example_method"
    assert repr(module) == "Module(google)"


def test_fullname(google):
    module = create_module(google, "examples.styles.google")
    c = get_by_name(module.classes, "ExampleClass")
    assert isinstance(c, Class)
    f = get_by_name(c.functions, "example_method")
    assert isinstance(f, Function)
    assert c.fullname == "examples.styles.google.ExampleClass"
    name = "examples.styles.google.ExampleClass.example_method"
    assert f.fullname == name


def test_relative_import():
    """# test module
    from .c import d
    from ..e import f
    """
    src = inspect.getdoc(test_relative_import)
    assert src
    node = ast.parse(src)
    module = create_module(node, "x.y.z")
    i = get_by_name(module.imports, "d")
    assert i
    assert i.fullname == "x.y.z.c.d"
    i = get_by_name(module.imports, "f")
    assert i
    assert i.fullname == "x.y.e.f"


def test_merge_items():
    """'''test'''
    def f(x: int=0, y: str='s')->bool:
        '''function.

        Args:
            x: parameter x.
            z: parameter z.

        Returns:
            Return True.'''
    """
    src = inspect.getdoc(test_merge_items)
    assert src
    node = ast.parse(src)
    module = create_module(node, "x")
    func = get_by_name(module.functions, "f")
    assert func
    merge_parameters(func)
    assert get_by_name(func.parameters, "x")
    assert get_by_name(func.parameters, "y")
    assert not get_by_name(func.parameters, "z")
    items = func.doc.get("Parameters").items  # type: ignore
    assert get_by_name(items, "x")
    assert get_by_name(items, "y")
    assert get_by_name(items, "z")
    assert [item.name for item in items] == ["x", "y", "z"]
    merge_returns(func)
    assert func.returns[0].type
    assert func.returns[0].text.str == "Return True."
    item = func.doc.get("Returns").items[0]  # type: ignore
    assert item.type.expr.id == "bool"  # type: ignore


def test_iter():
    """'''test module.'''
    m: str
    n = 1
    '''int: attribute n.'''
    class A(D):
        '''class.

        Attributes:
            a: attribute a.
        '''
        a: int
        def f(x: int, y: str) -> list[str]:
            '''function.'''
            class B(E,F.G):
                c: list
            raise ValueError
    """
    src = inspect.getdoc(test_iter)
    assert src
    node = ast.parse(src)
    module = create_module(node, "x")
    cls = get_by_name(module.classes, "A")
    assert cls
    func = get_by_name(cls.functions, "f")
    assert func
    cls = get_by_name(func.classes, "B")
    assert cls
    assert cls.fullname == "x.A.f.B"
    objs = iter_objects(module)
    assert next(objs).name == "x"
    assert next(objs).name == "A"
    assert next(objs).name == "f"
    assert next(objs).name == "B"
    merge_items(module)
    items = list(iter_items(module))
    for x in "mnaxyc":
        assert get_by_name(items, x)
    for x in ["x.A.f.B", "x.A.f", "F.G"]:
        assert get_by_name(items, x)
    assert get_by_name(items, "ValueError")
    assert any(isinstance(x, Return) for x in items)
    assert any(isinstance(x, Docstring) for x in items)
    assert any(isinstance(x, Item) for x in items)
    assert any(isinstance(x, Section) for x in items)
    assert any(isinstance(x, Parameters) for x in items)
    assert any(isinstance(x, Attributes) for x in items)
    assert any(isinstance(x, Raises) for x in items)
    assert any(isinstance(x, Returns) for x in items)
