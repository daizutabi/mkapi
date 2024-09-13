import ast
import inspect

import pytest


def test_create_module():
    from mkapi.object import create_module

    module = create_module("example._styles.google")
    assert module
    assert module.get("ExampleClass")


def test_create_function():
    from mkapi.object import Function, create_module
    from mkapi.utils import find_item_by_name

    module = create_module("example._styles.google")
    assert module
    func = module.get("module_level_function")
    assert isinstance(func, Function)
    assert func.name == "module_level_function"
    assert func.qualname == "module_level_function"
    assert len(func.parameters) == 4
    assert find_item_by_name(func.parameters, "param1")
    assert find_item_by_name(func.parameters, "param2")
    assert find_item_by_name(func.parameters, "args")
    assert find_item_by_name(func.parameters, "kwargs")
    assert len(func.raises) == 1


def test_iter_objects():
    from mkapi.object import create_module, iter_objects

    src = """'''test module.'''
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
    src = inspect.cleandoc(src)
    assert src
    node = ast.parse(src)
    module = create_module("test_iter_objects", node)
    assert module
    objs = iter_objects(module)
    assert next(objs).name == "m"
    assert next(objs).name == "n"
    assert next(objs).name == "A"
    assert next(objs).name == "a"
    assert next(objs).name == "f"
    assert next(objs).name == "B"
    assert next(objs).name == "c"


def test_get_object_kind_package():
    from mkapi.object import create_module, get_object_kind

    module = create_module("mkapi")
    assert module
    assert get_object_kind(module) == "package"


@pytest.fixture
def mkapi_objects():
    from mkapi.object import create_module

    module = create_module("mkapi.object")
    assert module
    return module


def test_get_object_kind_module(mkapi_objects):
    from mkapi.object import get_object_kind

    assert get_object_kind(mkapi_objects) == "module"
    assert mkapi_objects.kind == "module"


def test_get_object_kind_dataclass(mkapi_objects):
    from mkapi.object import get_object_kind

    cls = mkapi_objects.get("Object")
    assert get_object_kind(cls) == "dataclass"
    assert cls.kind == "dataclass"


def test_get_object_kind_function(mkapi_objects):
    from mkapi.object import get_object_kind

    func = mkapi_objects.get("create_function")
    assert get_object_kind(func) == "function"
    assert func.kind == "function"


def test_get_object_kind_method(mkapi_objects):
    from mkapi.object import get_object_kind

    cls = mkapi_objects.get("Object")
    method = cls.get("__post_init__")
    assert get_object_kind(method) == "method"
    assert method.kind == "method"


def test_get_object_kind_attribute(mkapi_objects):
    from mkapi.object import get_object_kind

    cls = mkapi_objects.get("Object")
    attribute = cls.get("node")
    assert get_object_kind(attribute) == "attribute"
    assert attribute.kind == "attribute"


def test_get_source_module(mkapi_objects):
    from mkapi.object import get_source

    s = get_source(mkapi_objects)
    assert s
    assert "def create_module(" in s


def test_get_source_function(mkapi_objects):
    from mkapi.object import get_source

    func = mkapi_objects.get("create_module")
    s = get_source(func)
    assert s
    assert s.startswith("def create_module")


def test_get_source_examples():
    from mkapi.object import create_module, get_source

    module = create_module("example._styles.google")
    assert module
    s = get_source(module)
    assert s
    assert s.startswith('"""Example')
    assert s.endswith("attr2: int\n")
    cls = module.get("ExampleClass")
    assert cls
    s = get_source(cls)
    assert s
    assert s.startswith("class ExampleClass")
    assert s.endswith("pass")


@pytest.fixture
def mkapiplugin():
    from mkapi.object import Class, create_module

    module = create_module("mkapi.plugin")
    assert module
    cls = module.get("MkApiPlugin")
    assert isinstance(cls, Class)
    return cls


@pytest.mark.parametrize("name", ["on_config", "dirty"])
def test_is_child(mkapiplugin, name):
    from mkapi.object import is_child

    for name_, obj in mkapiplugin.children.items():
        if name_ == name:
            assert is_child(obj, mkapiplugin)


@pytest.mark.parametrize("name", ["config_class", "config", "on_serve", "_is_protocol"])
def test_is_not_child(mkapiplugin, name):
    from mkapi.object import is_child

    for name_, obj in mkapiplugin.children.items():
        if name_ == name:
            assert not is_child(obj, mkapiplugin)


@pytest.mark.parametrize("attr", ["", ".example_method"])
def test_get_object_class(attr):
    from mkapi.object import get_object

    module = "example._styles.google"
    qualname = f"ExampleClass{attr}"
    x = get_object(f"example._styles.ExampleClassGoogle{attr}")
    assert x
    assert x.module == module
    assert x.qualname == qualname
    assert x.name == qualname.split(".")[-1]

    x = get_object(f"ExampleClassGoogle{attr}", "example._styles")
    assert x
    assert x.module == module
    assert x.qualname == qualname
    assert x.name == qualname.split(".")[-1]


def test_get_object_cache():
    from mkapi.object import Class, Function, create_module, get_object

    module = create_module("mkapi.object")
    a = get_object("mkapi.object")
    assert module is a
    c = get_object("mkapi.object.Object")
    f = get_object("mkapi.object.Module.__post_init__")
    assert isinstance(c, Class)
    assert c.module == "mkapi.object"
    assert isinstance(f, Function)
    assert f.module == "mkapi.object"
    c2 = get_object("mkapi.object.Object")
    f2 = get_object("mkapi.object.Module.__post_init__")
    assert c is c2
    assert f is f2


def test_get_fullname_from_object():
    from mkapi.object import get_fullname_from_object, get_object

    x = get_object("mkapi.object")
    assert x
    r = get_fullname_from_object("Object", x)
    assert r == "mkapi.object.Object"
    x = get_object(r)
    assert x
    r = get_fullname_from_object("__repr__", x)
    assert r == "mkapi.object.Object.__repr__"
    x = get_object(r)
    assert x
    r = get_fullname_from_object("__post_init__", x)
    assert r == "mkapi.object.Object.__post_init__"
    x = get_object(r)
    assert x
    r = get_fullname_from_object("Object", x)
    assert r == "mkapi.object.Object"


def test_get_object_asname():
    from mkapi.object import get_object

    name = "example._styles.ExampleClassGoogle.example_method"
    obj = get_object(name)
    assert obj
    assert obj.name == "example_method"
    assert obj.module == "example._styles.google"
    assert obj.fullname == "example._styles.google.ExampleClass.example_method"


def test_get_object_export():
    from mkapi.object import get_object

    name = "jinja2.Environment.compile"
    obj = get_object(name)
    assert obj
    assert obj.name == "compile"
    assert obj.module == "jinja2.environment"
    assert obj.fullname == "jinja2.environment.Environment.compile"
