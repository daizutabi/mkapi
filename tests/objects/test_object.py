import ast

from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Module,
    create_module,
    get_kind,
    get_source,
    walk,
)
from mkapi.utils import get_by_name


def test_class_parameters():
    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    assert len(cls.parameters) == 3
    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    assert get_by_name(cls.parameters, "name")
    assert get_by_name(cls.parameters, "dict")


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


# def test_get_source(google, source, get):
#     module = _create_module("google", google, source)
#     x = get_source(module)
#     assert x
#     assert x.startswith('"""Example')
#     assert x.endswith("attr2: int\n")
#     node = get("ExampleClass")
#     cls = create_class(node, module, None)
#     x = get_source(cls)
#     assert x
#     assert x.startswith("class ExampleClass")
#     assert x.endswith("pass\n")


# def test_get_object():
#     module = create_module("mkapi.objects")
#     a = get_object("mkapi.objects")
#     assert module is a
#     c = get_object("mkapi.objects.Object")
#     f = get_object("mkapi.objects.Module.__post_init__")
#     assert isinstance(c, Class)
#     assert c.module is module
#     assert isinstance(f, Function)
#     assert f.module is module
#     c2 = get_object("mkapi.objects.Object")
#     f2 = get_object("mkapi.objects.Module.__post_init__")
#     assert c is c2
#     assert f is f2
#     m1 = create_module("mkdocs.structure.files")
#     m2 = create_module("mkdocs.structure.files")
#     assert m1 is m2


# def test_iter_base_classes():
#     cls = get_object("mkapi.plugins.MkAPIPlugin")
#     assert isinstance(cls, Class)
#     assert cls.qualname.str == "MkAPIPlugin"
#     assert cls.fullname.str == "mkapi.plugins.MkAPIPlugin"
#     func = get_by_name(cls.functions, "on_config")
#     assert func
#     assert func.qualname.str == "MkAPIPlugin.on_config"
#     assert func.fullname.str == "mkapi.plugins.MkAPIPlugin.on_config"
#     base = next(iter_base_classes(cls))
#     assert base.name.str == "BasePlugin"
#     assert base.fullname.str == "mkdocs.plugins.BasePlugin"
#     func = get_by_name(base.functions, "on_config")
#     assert func
#     assert func.qualname.str == "BasePlugin.on_config"
#     assert func.fullname.str == "mkdocs.plugins.BasePlugin.on_config"
#     cls = get_object("mkapi.plugins.MkAPIConfig")
#     assert isinstance(cls, Class)
#     base = next(iter_base_classes(cls))
#     assert base.name.str == "Config"
#     assert base.qualname.str == "Config"
#     assert base.fullname.str == "mkdocs.config.base.Config"


# def test_inherit_base_classes():
#     cache_clear()
#     create_module("mkapi.plugins")
#     cls = get_object("mkapi.plugins.MkAPIConfig")
#     assert isinstance(cls, Class)
#     assert get_by_name(cls.attributes, "config_file_path")
#     cls = get_object("mkapi.plugins.MkAPIPlugin")
#     assert isinstance(cls, Class)
#     assert get_by_name(cls.functions, "on_page_read_source")
#     cls = get_object("mkapi.items.Parameters")
#     assert isinstance(cls, Class)
#     assert get_by_name(cls.attributes, "name")
#     assert get_by_name(cls.attributes, "type")
#     assert get_by_name(cls.attributes, "items")


# def test_iter_dataclass_parameters():
#     cls = get_object("mkapi.items.Parameters")
#     assert isinstance(cls, Class)
#     p = cls.parameters
#     assert len(p) == 5
#     assert p[0].name.str == "name"
#     assert p[1].name.str == "type"
#     assert p[2].name.str == "text"
#     assert p[3].name.str == "items"
#     assert p[4].name.str == "kind"


# def test_inherit_base_classes_order():
#     module = create_module("mkapi.plugins")
#     assert isinstance(module, Module)
#     cls = get_by_name(module.classes, "MkAPIPlugin")
#     assert isinstance(cls, Class)
#     indexes = []
#     for name in ["on_startup", "on_nav", "on_shutdown", "on_env", "on_post_page"]:
#         func = get_by_name(cls.functions, name)
#         assert func
#         indexes.append(cls.functions.index(func))
#     assert indexes == sorted(indexes)
#     indexes.clear()
#     for name in ["api_dirs", "pages", "config_class", "config"]:
#         attr = get_by_name(cls.attributes, name)
#         assert attr
#         indexes.append(cls.attributes.index(attr))
#     assert indexes == sorted(indexes)


# def test_get_object_nest():
#     cache_clear()
#     assert get_object("mkapi.items.Name.__repr__")
#     assert get_object("mkapi.items.Name")


# def test_load_module():
#     cache_clear()
#     module = load_module("examples.styles.google")
#     assert module
#     cls = get_by_name(module.classes, "ExampleClass")
#     assert isinstance(cls, Class)
#     assert not get_by_name(cls.functions, "__init__")
#     cache_clear()
#     module = load_module("examples.styles")
#     assert module
#     assert get_by_name(module.classes, "ExampleClassGoogle")
#     assert get_by_name(module.classes, "ExampleClassNumPy")


# def test_get_object_using_all():
#     cache_clear()
#     assert get_object("schemdraw.Drawing")
#     assert get_object("schemdraw.svgconfig")
#     assert get_object("examples.styles.ExampleClassGoogle")
#     assert get_object("examples.styles.ExampleClassNumPy")
#     assert get_object("examples.styles.ExampleClassGoogle.attr1")
