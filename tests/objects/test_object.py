import ast
import inspect

import pytest


def test_create_module():
    from mkapi.objects import create_module

    module = create_module("examples.styles.google")
    assert module
    assert module.get("ExampleClass")


def test_create_function():
    from mkapi.objects import Function, create_module
    from mkapi.utils import get_by_name

    module = create_module("examples.styles.google")
    assert module
    func = module.get("module_level_function")
    assert isinstance(func, Function)
    assert func.name == "module_level_function"
    assert func.qualname == "module_level_function"
    assert len(func.parameters) == 4
    assert get_by_name(func.parameters, "param1")
    assert get_by_name(func.parameters, "param2")
    assert get_by_name(func.parameters, "args")
    assert get_by_name(func.parameters, "kwargs")
    assert len(func.raises) == 1


def test_iter_objects():
    from mkapi.objects import create_module, iter_objects

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
    module = create_module("x", node)
    assert module
    objs = iter_objects(module)
    assert next(objs).name == "m"
    assert next(objs).name == "n"
    assert next(objs).name == "A"
    assert next(objs).name == "a"
    assert next(objs).name == "f"
    assert next(objs).name == "B"
    assert next(objs).name == "c"


def test_kind_package():
    from mkapi.objects import create_module, get_kind

    module = create_module("mkapi")
    assert module
    assert get_kind(module) == "package"


@pytest.fixture
def mkapi_objects():
    from mkapi.objects import create_module

    module = create_module("mkapi.objects")
    assert module
    return module


def test_kind_module(mkapi_objects):
    from mkapi.objects import get_kind

    assert get_kind(mkapi_objects) == "module"


def test_kind_dataclass(mkapi_objects):
    from mkapi.objects import get_kind

    cls = mkapi_objects.get("Object")
    assert get_kind(cls) == "dataclass"


def test_kind_function(mkapi_objects):
    from mkapi.objects import get_kind

    func = mkapi_objects.get("create_function")
    assert get_kind(func) == "function"


def test_kind_method(mkapi_objects):
    from mkapi.objects import get_kind

    cls = mkapi_objects.get("Object")
    method = cls.get("__post_init__")
    assert get_kind(method) == "method"


def test_kind_attribute(mkapi_objects):
    from mkapi.objects import get_kind

    cls = mkapi_objects.get("Object")
    attribute = cls.get("node")
    assert get_kind(attribute) == "attribute"


def test_get_source_module(mkapi_objects):
    from mkapi.objects import get_source

    s = get_source(mkapi_objects)
    assert s
    assert "def create_module(" in s


def test_get_source_function(mkapi_objects):
    from mkapi.objects import get_source

    func = mkapi_objects.get("create_module")
    s = get_source(func)
    assert s
    assert s.startswith("def create_module")


def test_get_source_examples():
    from mkapi.objects import create_module, get_source

    module = create_module("examples.styles.google")
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
    from mkapi.objects import Class, create_module

    module = create_module("mkapi.plugins")
    assert module
    cls = module.get("MkAPIPlugin")
    assert isinstance(cls, Class)
    return cls


@pytest.mark.parametrize("name", ["api_dirs", "on_config", "on_serve", "dirty"])
def test_is_child(mkapiplugin, name):
    from mkapi.objects import is_child

    for name_, obj in mkapiplugin.children.items():
        if name_ == name:
            assert is_child(obj, mkapiplugin)


@pytest.mark.parametrize("name", ["config_class", "config", "on_post_build", "_is_protocol"])
def test_is_not_child(mkapiplugin, name):
    from mkapi.objects import is_child

    for name_, obj in mkapiplugin.children.items():
        if name_ == name:
            assert not is_child(obj, mkapiplugin)


@pytest.mark.parametrize("attr", ["", ".attr1"])
def test_get_object_class(attr):
    from mkapi.objects import get_object

    module = "examples.styles.google"
    qualname = f"ExampleClass{attr}"
    x = get_object(f"examples.styles.ExampleClassGoogle{attr}")
    assert x
    assert x.module == module
    assert x.qualname == qualname
    assert x.name == qualname.split(".")[-1]

    x = get_object(f"ExampleClassGoogle{attr}", "examples.styles")
    assert x
    assert x.module == module
    assert x.qualname == qualname
    assert x.name == qualname.split(".")[-1]


def test_get_object_cache():
    from mkapi.objects import Class, Function, create_module, get_object

    module = create_module("mkapi.objects")
    a = get_object("mkapi.objects")
    assert module is a
    c = get_object("mkapi.objects.Object")
    f = get_object("mkapi.objects.Module.__post_init__")
    assert isinstance(c, Class)
    assert c.module == "mkapi.objects"
    assert isinstance(f, Function)
    assert f.module == "mkapi.objects"
    c2 = get_object("mkapi.objects.Object")
    f2 = get_object("mkapi.objects.Module.__post_init__")
    assert c is c2
    assert f is f2


def test_get_fullname_from_object():
    from mkapi.objects import get_fullname_from_object, get_object

    x = get_object("mkapi.objects")
    assert x
    r = get_fullname_from_object("Object", x)
    assert r == "mkapi.objects.Object"
    x = get_object(r)
    assert x
    r = get_fullname_from_object("__repr__", x)
    assert r == "mkapi.objects.Object.__repr__"
    x = get_object(r)
    assert x
    r = get_fullname_from_object("__post_init__", x)
    assert r == "mkapi.objects.Object.__post_init__"
    x = get_object(r)
    assert x
    r = get_fullname_from_object("Object", x)
    assert r == "mkapi.objects.Object"


@pytest.fixture
def google():
    from mkapi.objects import Module, get_object

    module = get_object("examples.styles.google")
    assert isinstance(module, Module)
    return module


@pytest.fixture(params=["module_level_variable1", "module_level_function", "ExampleClass"])
def name(request):
    return request.param


def test_get_members_examples(google, name):
    from mkapi.objects import get_members

    assert name in get_members(google)


def test_get_members_examples_class(google, name):
    from mkapi.objects import Class, get_members

    m = get_members(google, lambda x: isinstance(x, Class))
    if "Class" in name:
        assert name in m
    else:
        assert name not in m


def test_get_members_examples_function(google, name):
    from mkapi.objects import Function, get_members

    m = get_members(google, lambda x: isinstance(x, Function))
    if "function" in name:
        assert name in m
    else:
        assert name not in m


def test_get_members_examples_attribute(google, name):
    from mkapi.objects import Attribute, get_members

    m = get_members(google, lambda x: isinstance(x, Attribute))
    if "variable" in name:
        assert name in m
    else:
        assert name not in m


@pytest.mark.parametrize("name", ["attr1", "__init__"])
def test_get_members_name(google, name):
    from mkapi.objects import Class, get_members

    cls = google.get("ExampleClass")
    assert isinstance(cls, Class)

    m = get_members(cls)
    assert name in m

    m = get_members(cls, lambda x: "_" not in x.name)
    if "_" in name:
        assert name not in m
    else:
        assert name in m


@pytest.mark.parametrize("name", ["__all__", "ExampleClassGoogle", "ExampleClassNumPy"])
def test_get_members_asname(name):
    from mkapi.objects import create_module, get_members

    module = create_module("examples.styles")
    assert module
    assert name in get_members(module)


#     assert a
#     b = create_module("examples.styles.google")
#     assert b

#     x = a.get("ExampleClassGoogle")
#     assert x
#     print(x, id(x), x.node)

#     x = b.get("ExampleClass")
#     assert x
#     print(x, id(x), x.node)
#     assert 0

# def test_iter_objects_predicate():


#     module = create_module("mkapi.plugins")
#     assert module
#     cls = module.get("MkAPIPlugin")
#     assert isinstance(cls, Class)
#     x = list(iter_objects(cls))
#     members = ["MkAPIPlugin", "on_nav", "pages"]
#     others = ["load_config", "config"]
#     for name in members:
#         assert get_by_name(x, name)
#     for name in others:
#         assert get_by_name(x, name)

#     def predicate(obj, parent):
#         if parent is None:
#             return True

#         return obj.module is parent.module

#     x = list(iter_objects(cls, predicate=predicate))
#     for name in members:
#         assert get_by_name(x, name)
#     for name in others:
#         assert not get_by_name(x, name)


# def test_iter_object_package():
#     module = create_module("examples.styles")
#     assert module
#     for x in iter_objects(module):
#         print(x)
