import ast
import inspect

from mkapi.objects import (
    Class,
    Function,
    Property,
    create_class,
    create_module,
    get_object,
)
from mkapi.utils import get_by_name


def test_create_class_nested():
    src = """
    class A:
        class B:
            class C:
                pass
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert len(cls.children) == 1
    cls = cls.children["B"]
    assert isinstance(cls, Class)
    assert len(cls.children) == 1
    cls = cls.children["C"]
    assert isinstance(cls, Class)


def test_create_class(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert isinstance(cls, Class)
    assert cls.name == "ExampleClass"
    assert len(cls.raises) == 0
    for x in ["_private"]:
        assert isinstance(cls.get(x), Function)
    for x in ["readonly_property", "readwrite_property"]:
        assert isinstance(cls.get(x), Property)


def test_inherit():
    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    func = cls.get("__repr__")
    assert isinstance(func, Function)
    assert func.qualname == "Object.__repr__"


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
    assert get_by_name(cls.parameters, "node")
    assert get_by_name(cls.parameters, "module")
    assert get_by_name(cls.parameters, "parent")


# def test_base_classes():
#     cls = get_object("mkapi.plugins.MkAPIPlugin")
#     assert isinstance(cls, Class)
#     assert cls.qualname == "MkAPIPlugin"
#     func = cls.get("on_config")
#     assert isinstance(func, Function)
#     assert func.qualname == "MkAPIPlugin.on_config"
#     bases = list(_iter_base_classes(cls.name, cls.module))
#     assert bases == [("BasePlugin", "mkdocs.plugins")]
#     base = next(iter_base_classes(cls.name, cls.module))
#     assert base.name == "BasePlugin"
#     assert base.module == "mkdocs.plugins"
#     func = base.get("on_config")
#     assert func
#     assert func.qualname == "BasePlugin.on_config"
#     assert func.module == "mkdocs.plugins"
#     cls = get_object("mkapi.plugins.MkAPIConfig")
#     assert isinstance(cls, Class)
#     base = next(iter_base_classes(cls.name, cls.module))
#     assert base.name == "Config"
#     assert base.qualname == "Config"
#     assert base.module == "mkdocs.config.base"


def test_inherit_base_classes():
    create_module("mkapi.plugins")
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    assert cls.get("config_file_path")
    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    assert cls.get("on_page_read_source")
    cls = get_object("mkapi.objects.Parameter")
    assert isinstance(cls, Class)
    assert cls.get("name")
    assert cls.get("type")
    assert cls.get("default")


def test_iter_dataclass_parameters():
    cls = get_object("mkapi.objects.Parameter")
    assert isinstance(cls, Class)
    p = cls.parameters
    assert p[0].name == "name"
    assert p[1].name == "type"
    assert p[2].name == "default"
    assert p[3].name == "kind"


# def test_inherit_base_classes_order():
#     module = create_module("mkapi.plugins")
#     assert isinstance(module, Module)
#     cls = module.get( "MkAPIPlugin")
#     assert isinstance(cls, Class)
#     indexes = []
#     for name in ["on_startup", "on_nav", "on_shutdown", "on_env", "on_post_page"]:
#         func = cls.get(name)
#         assert func
#         indexes.append(cls.functions.index(func))
#     assert indexes == sorted(indexes)
#     indexes.clear()
#     for name in ["api_dirs", "pages", "config_class", "config"]:
#         attr = get_by_name(cls.attributes, name)
#         assert attr
#         indexes.append(cls.attributes.index(attr))
#     assert indexes == sorted(indexes)
