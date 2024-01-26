import ast
import inspect
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.objects import (
    Class,
    Function,
    create_class,
    create_function,
    create_module,
    iter_objects,
    merge_items,
    objects,
)
from mkapi.utils import get_by_name, get_module_node


@pytest.fixture(scope="module")
def google():
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    return get_module_node("examples.styles.example_google")


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
    assert len(func.doc.sections) == 3
    assert repr(func) == "Function('module_level_function')"


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
    assert get_by_name(cls.attributes, "readonly_property")
    assert get_by_name(cls.attributes, "readwrite_property")
    func = get_by_name(cls.functions, "__init__")
    assert isinstance(func, Function)
    assert func.qualname == "ExampleClass.__init__"
    assert func.fullname == "__mkapi__.ExampleClass.__init__"
    assert repr(cls) == "Class('ExampleClass')"


def test_create_module(google):
    module = create_module("google", google)
    assert module.name == "google"
    assert len(module.functions) == 4
    assert len(module.classes) == 3
    cls = get_by_name(module.classes, "ExampleClass")
    assert isinstance(cls, Class)
    assert cls.fullname == "google.ExampleClass"
    func = get_by_name(cls.functions, "example_method")
    assert isinstance(func, Function)
    assert func.fullname == "google.ExampleClass.example_method"
    assert repr(module) == "Module('google')"


def test_fullname(google):
    module = create_module("examples.styles.google", google)
    c = get_by_name(module.classes, "ExampleClass")
    assert isinstance(c, Class)
    f = get_by_name(c.functions, "example_method")
    assert isinstance(f, Function)
    assert c.fullname == "examples.styles.google.ExampleClass"
    name = "examples.styles.google.ExampleClass.example_method"
    assert f.fullname == name


def test_kind():
    node = get_module_node("mkapi")
    assert node
    module = create_module("mkapi", node)
    assert module.kind == "package"
    node = get_module_node("mkapi.objects")
    assert node
    module = create_module("mkapi.objects", node)
    assert module
    assert module.kind == "module"
    cls = get_by_name(module.classes, "Object")
    assert cls
    assert cls.kind == "class"
    func = get_by_name(module.functions, "create_function")
    assert func
    assert func.kind == "function"
    method = get_by_name(cls.functions, "__post_init__")
    assert method
    assert method.kind == "method"
    prop = get_by_name(cls.attributes, "kind")
    assert prop
    assert prop.kind == "property"
    attr = get_by_name(cls.attributes, "node")
    assert attr
    assert attr.kind == "attribute"


def test_merge_items():
    """'''test'''
    def f(x: int = 0, y: str = 's') -> bool:
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
    module = create_module("x", node)
    func = get_by_name(module.functions, "f")
    assert func
    # merge_parameters(func)
    assert get_by_name(func.parameters, "x")
    assert get_by_name(func.parameters, "y")
    assert not get_by_name(func.parameters, "z")
    items = get_by_name(func.doc.sections, "Parameters").items  # type: ignore
    assert get_by_name(items, "x")
    assert get_by_name(items, "y")
    assert get_by_name(items, "z")
    assert [item.name for item in items] == ["x", "y", "z"]
    # merge_returns(func)
    assert func.returns[0].type
    assert func.returns[0].text.str == "Return True."
    item = get_by_name(func.doc.sections, "Returns").items[0]  # type: ignore
    assert item.type.expr.id == "bool"  # type: ignore


def test_iter_objects():
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
    src = inspect.getdoc(test_iter_objects)
    assert src
    node = ast.parse(src)
    module = create_module("x", node)
    cls = get_by_name(module.classes, "A")
    assert cls
    func = get_by_name(cls.functions, "f")
    assert func
    cls = get_by_name(func.classes, "B")
    assert cls
    assert cls.fullname == "x.A.f.B"
    objs = iter_objects(module)
    assert next(objs).name == "x"
    assert next(objs).name == "m"
    assert next(objs).name == "n"
    assert next(objs).name == "A"
    assert next(objs).name == "a"
    assert next(objs).name == "f"
    merge_items(module)


def test_iter_objects_polars():
    name = "polars.dataframe.frame"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    x = list(iter_objects(module, 0))
    assert len(x) == 1
    x = list(iter_objects(module, 1))
    assert get_by_name(x, "DataFrame")
    assert not get_by_name(x, "product")
    x = list(iter_objects(module, 2))
    assert get_by_name(x, "DataFrame")
    assert get_by_name(x, "product")


def test_set_markdown():
    name = "mkapi.plugins"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    assert module.doc.type.markdown == "[mkapi][__mkapi__.mkapi].plugins"
    obj = get_by_name(module.classes, "MkAPIPlugin")
    assert isinstance(obj, Class)
    m = obj.doc.type.markdown
    assert "[mkapi][__mkapi__.mkapi]." in m
    assert ".[plugins][__mkapi__.mkapi.plugins].MkAPIPlugin" in m
    m = obj.bases[0].type.markdown
    assert "[BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin]" in m
    assert "[[MkAPIConfig][__mkapi__.mkapi.plugins.MkAPIConfig]]" in m
    name = "mkapi.items"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    obj = get_by_name(module.functions, "iter_raises")
    assert isinstance(obj, Function)
    m = obj.doc.text.markdown
    assert m == "Yield [Raise][__mkapi__.mkapi.items.Raise] instances."


def test_set_markdown_polars():
    name = "polars.dataframe.frame"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    obj = get_by_name(module.classes, "DataFrame")
    assert isinstance(obj, Class)
    m = obj.doc.type.markdown
    assert "[polars][__mkapi__.polars].[dataframe]" in m
    assert "[__mkapi__.polars.dataframe].[frame]" in m
    assert "[__mkapi__.polars.dataframe.frame].DataFrame" in m
