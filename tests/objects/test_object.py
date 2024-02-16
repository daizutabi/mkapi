import ast
import inspect

from mkapi.importlib import load_module
from mkapi.objects import Class, Function, Module, create_module, iter_objects
from mkapi.utils import get_by_name, get_module_node


def test_fullname(google):
    module = create_module("examples.styles.google", google)
    c = get_by_name(module.classes, "ExampleClass")
    assert isinstance(c, Class)
    f = get_by_name(c.functions, "example_method")
    assert isinstance(f, Function)
    assert c.fullname.str == "examples.styles.google.ExampleClass"
    name = "examples.styles.google.ExampleClass.example_method"
    assert f.fullname.str == name


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
    assert cls.fullname.str == "x.A.f.B"
    objs = iter_objects(module)
    assert next(objs).name.str == "x"
    assert next(objs).name.str == "A"
    assert next(objs).name.str == "f"
    assert next(objs).name.str == "B"
    assert next(objs).name.str == "c"
    assert next(objs).name.str == "a"
    assert next(objs).name.str == "m"
    assert next(objs).name.str == "n"


def test_iter_objects_predicate():
    module = load_module("mkapi.plugins")
    assert isinstance(module, Module)
    cls = get_by_name(module.classes, "MkAPIPlugin")
    assert isinstance(cls, Class)
    x = list(iter_objects(cls))
    members = ["MkAPIPlugin", "on_nav", "pages"]
    others = ["load_config", "config"]
    for name in members:
        assert get_by_name(x, name)
    for name in others:
        assert get_by_name(x, name)

    def predicate(obj, parent):
        if parent is None:
            return True
        return obj.module is parent.module

    x = list(iter_objects(cls, predicate=predicate))
    for name in members:
        assert get_by_name(x, name)
    for name in others:
        assert not get_by_name(x, name)


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
    assert cls.kind == "dataclass"
    func = get_by_name(module.functions, "create_function")
    assert func
    assert func.kind == "function"
    method = get_by_name(cls.functions, "__post_init__")
    assert method
    assert method.kind == "method"
    attr = get_by_name(cls.attributes, "node")
    assert attr
    assert attr.kind == "attribute"
