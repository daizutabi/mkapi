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


def test_kind():
    from mkapi.objects import Attribute, Class, Function, create_module, get_kind

    module = create_module("mkapi")
    assert module
    assert get_kind(module) == "package"
    module = create_module("mkapi.objects")
    assert module
    assert get_kind(module) == "module"
    cls = module.get("Object")
    assert isinstance(cls, Class)
    assert get_kind(cls) == "dataclass"
    func = module.get("create_function")
    assert isinstance(func, Function)
    assert get_kind(func) == "function"
    method = cls.get("__post_init__")
    assert isinstance(method, Function)
    assert method
    assert get_kind(method) == "method"
    assign = cls.get("node")
    assert isinstance(assign, Attribute)
    assert get_kind(assign) == "attribute"


def test_get_source():
    from mkapi.objects import Class, Function, create_module, get_source

    module = create_module("mkapi.objects")
    assert module
    s = get_source(module)
    assert s
    assert "def create_module(" in s
    func = module.get("create_module")
    assert isinstance(func, Function)
    assert func
    s = get_source(func)
    assert s
    assert s.startswith("def create_module")

    module = create_module("examples.styles.google")
    assert module
    s = get_source(module)
    assert s
    assert s.startswith('"""Example')
    assert s.endswith("attr2: int\n")
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    s = get_source(cls)
    assert s
    assert s.startswith("class ExampleClass")
    assert s.endswith("pass")


def test_is_child():
    from mkapi.objects import Class, create_module, is_child

    module = create_module("mkapi.plugins")
    assert module
    cls = module.get("MkAPIPlugin")
    assert isinstance(cls, Class)
    for name, obj in cls.children.items():
        for x in ["api_dirs", "on_config", "on_serve", "dirty"]:
            if name == x:
                assert is_child(obj, cls)
        for x in ["config_class", "config", "on_post_build", "_is_protocol"]:
            if name == x:
                assert not is_child(obj, cls)


def test_resolve():
    from mkapi.objects import resolve

    fullname = "examples.styles.ExampleClassGoogle"
    x = resolve(fullname)
    assert x
    assert x[0] == "ExampleClass"
    assert x[1] == "examples.styles.google"

    fullname = "mkapi.objects.ast"
    x = resolve(fullname)
    assert x
    assert x[0] == "ast"
    assert not x[1]

    fullname = "mkapi.objects.mkapi.ast"
    x = resolve(fullname)
    assert x
    assert x[0] == "mkapi.ast"
    assert not x[1]

    fullname = "mkapi.objects.mkapi.ast.iter_parameters"
    x = resolve(fullname)
    assert x
    assert x[0] == "iter_parameters"
    assert x[1] == "mkapi.ast"


def test_get_object():
    from mkapi.objects import get_object

    fullname = "examples.styles.ExampleClassGoogle"
    x = get_object(fullname)
    assert x
    assert x.module == "examples.styles.google"
    assert x.name == "ExampleClass"

    fullname = "examples.styles.ExampleClassGoogle.attr1"
    x = get_object(fullname)
    assert x
    assert x.module == "examples.styles.google"
    assert x.name == "attr1"
    assert x.qualname == "ExampleClass.attr1"


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
