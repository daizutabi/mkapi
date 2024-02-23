from mkapi.objects import (
    Attribute,
    Class,
    Function,
    create_module,
    get_object,
    get_source,
)


def test_get_object():
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


def test_create_module():
    module = create_module("examples.styles.google")
    assert module
    assert module.get("ExampleClass")
    module = create_module("examples.styles")
    assert module
    assert module.get("ExampleClassGoogle")
    assert module.get("ExampleClassNumPy")


def test_get_source():
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


# def test_iter_objects():
#     """'''test module.'''
#     m: str
#     n = 1
#     '''int: attribute n.'''
#     class A(D):
#         '''class.

#         Attributes:
#             a: attribute a.
#         '''
#         a: int
#         def f(x: int, y: str) -> list[str]:
#             '''function.'''
#             class B(E,F.G):
#                 c: list
#             raise ValueError
#     """
#     src = inspect.getdoc(test_iter_objects)
#     assert src
#     node = ast.parse(src)
#     module = _create_module("x", node)
#     cls = get_by_name(module.classes, "A")
#     assert cls
#     func = get_by_name(cls.functions, "f")
#     assert func
#     cls = get_by_name(func.classes, "B")
#     assert cls
#     assert cls.fullname.str == "x.A.f.B"
#     objs = iter_objects(module)
#     assert next(objs).name.str == "x"
#     assert next(objs).name.str == "A"
#     assert next(objs).name.str == "f"
#     assert next(objs).name.str == "B"
#     assert next(objs).name.str == "c"
#     assert next(objs).name.str == "a"
#     assert next(objs).name.str == "m"
#     assert next(objs).name.str == "n"


# def test_iter_objects_predicate():
#     module = create_module("mkapi.plugins")
#     assert isinstance(module, Module)
#     cls = get_by_name(module.classes, "MkAPIPlugin")
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
