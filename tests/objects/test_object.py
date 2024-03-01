import ast
import inspect


def test_create_module():
    from mkapi.objects import create_module

    module = create_module("examples.styles.google")
    assert module
    assert module.get("ExampleClass")
    module = create_module("examples.styles")
    assert module
    assert not module.get("ExampleClassGoogle")
    assert not module.get("ExampleClassNumPy")


def test_kind():
    from mkapi.objects import Attribute, Class, Function, create_module

    module = create_module("mkapi")
    assert module
    assert module.kind == "package"
    module = create_module("mkapi.objects")
    assert module
    assert module.kind == "module"
    cls = module.get("Object")
    assert isinstance(cls, Class)
    assert cls.kind == "dataclass"
    func = module.get("create_function")
    assert isinstance(func, Function)
    assert func.kind == "function"
    method = cls.get("__post_init__")
    assert isinstance(method, Function)
    assert method
    assert method.kind == "method"
    assign = cls.get("node")
    assert isinstance(assign, Attribute)
    assert assign.kind == "attribute"


def test_iter_objects():
    from mkapi.objects import Class, Function, create_module, iter_objects

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
    cls = module.get("A")
    assert isinstance(cls, Class)
    func = cls.get("f")
    assert isinstance(func, Function)
    cls = func.get("B")
    assert isinstance(cls, Class)
    assert cls.fullname == "x.A.f.B"
    objs = iter_objects(module)
    assert next(objs).name == "m"
    assert next(objs).name == "n"
    assert next(objs).name == "A"
    assert next(objs).name == "a"
    assert next(objs).name == "f"
    assert next(objs).name == "B"
    assert next(objs).name == "c"
