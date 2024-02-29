import ast
import inspect


def test_create_module():
    from mkapi.objects import create_module

    module = create_module("examples.styles.google")
    assert module
    assert module.get("ExampleClass")
    module = create_module("examples.styles")
    assert module
    assert module.get("ExampleClassGoogle")
    assert module.get("ExampleClassNumPy")


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


def test_is_member():
    from mkapi.objects import Class, get_object, is_member

    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    for name, obj in cls.children.items():
        for x in ["api_dirs", "on_config", "on_serve", "dirty"]:
            if name == x:
                assert is_member(obj, cls)
        for x in ["config_class", "config", "on_post_build", "_is_protocol"]:
            if name == x:
                assert not is_member(obj, cls)


def test_iter_objects():
    from mkapi.objects import Class, Function, _create_module, iter_objects

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
    module = _create_module("x", node)
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


def test_get_object():
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
    m1 = create_module("mkdocs.structure.files")
    m2 = create_module("mkdocs.structure.files")
    assert m1 is m2
    assert get_object("examples.styles.ExampleClassGoogle")


def test_get_object_schemdraw():
    from mkapi.objects import aliases, get_object

    assert get_object("schemdraw")
    assert "schemdraw.Drawing" in aliases["schemdraw.schemdraw.Drawing"]
    x = get_object("schemdraw.svgconfig")
    assert x
    assert x.fullname == "schemdraw.backends.svg.config"
    x = get_object("schemdraw.Drawing")
    assert x
    assert x.fullname == "schemdraw.schemdraw.Drawing"
