from mkapi.importlib import (
    get_object,
    get_source,
    # inherit_base_classes,
    iter_base_classes,
    load_module,
)
from mkapi.objects import Class, Function, Module
from mkapi.utils import cache_clear, get_by_name


def test_load_module_source():
    module = load_module("mkdocs.structure.files")
    assert module
    assert module.source
    assert "class File" in module.source
    module = load_module("mkapi.plugins")
    assert module
    cls = get_by_name(module.classes, "MkAPIConfig")
    assert cls
    assert cls.module is module
    src = get_source(cls)
    assert src
    assert src.startswith("class MkAPIConfig")
    src = get_source(module)
    assert src
    assert "MkAPIPlugin" in src


def test_get_object():
    module = load_module("mkapi.objects")
    a = get_object("mkapi.objects")
    assert module is a
    c = get_object("mkapi.objects.Object")
    f = get_object("mkapi.objects.Module.__post_init__")
    assert isinstance(c, Class)
    assert c.module is module
    assert isinstance(f, Function)
    assert f.module is module
    c2 = get_object("mkapi.objects.Object")
    f2 = get_object("mkapi.objects.Module.__post_init__")
    assert c is c2
    assert f is f2
    m1 = load_module("mkdocs.structure.files")
    m2 = load_module("mkdocs.structure.files")
    assert m1 is m2


def test_iter_base_classes():
    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    assert cls.qualname.str == "MkAPIPlugin"
    assert cls.fullname.str == "mkapi.plugins.MkAPIPlugin"
    func = get_by_name(cls.functions, "on_config")
    assert func
    assert func.qualname.str == "MkAPIPlugin.on_config"
    assert func.fullname.str == "mkapi.plugins.MkAPIPlugin.on_config"
    base = next(iter_base_classes(cls))
    assert base.name.str == "BasePlugin"
    assert base.fullname.str == "mkdocs.plugins.BasePlugin"
    func = get_by_name(base.functions, "on_config")
    assert func
    assert func.qualname.str == "BasePlugin.on_config"
    assert func.fullname.str == "mkdocs.plugins.BasePlugin.on_config"
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    base = next(iter_base_classes(cls))
    assert base.name.str == "Config"
    assert base.qualname.str == "Config"
    assert base.fullname.str == "mkdocs.config.base.Config"


def test_inherit_base_classes():
    load_module("mkapi.plugins")
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    # inherit_base_classes(cls)
    assert get_by_name(cls.attributes, "config_file_path")
    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    # inherit_base_classes(cls)
    assert get_by_name(cls.functions, "on_page_read_source")
    cls = get_object("mkapi.items.Parameters")
    assert isinstance(cls, Class)
    assert get_by_name(cls.attributes, "name")
    assert get_by_name(cls.attributes, "type")
    assert get_by_name(cls.attributes, "items")


def test_iter_dataclass_parameters():
    cls = get_object("mkapi.items.Parameters")
    assert isinstance(cls, Class)
    p = cls.parameters
    assert len(p) == 5
    assert p[0].name.str == "name"
    assert p[1].name.str == "type"
    assert p[2].name.str == "text"
    assert p[3].name.str == "items"
    assert p[4].name.str == "kind"


def test_inherit_base_classes_order():
    module = load_module("mkapi.plugins")
    assert isinstance(module, Module)
    cls = get_by_name(module.classes, "MkAPIPlugin")
    assert isinstance(cls, Class)
    indexes = []
    for name in ["on_startup", "on_nav", "on_shutdown", "on_env", "on_post_page"]:
        func = get_by_name(cls.functions, name)
        assert func
        indexes.append(cls.functions.index(func))
    assert indexes == sorted(indexes)
    indexes.clear()
    for name in ["api_dirs", "pages", "config_class", "config"]:
        attr = get_by_name(cls.attributes, name)
        assert attr
        indexes.append(cls.attributes.index(attr))
    assert indexes == sorted(indexes)


def test_get_object_using_all():
    cache_clear()
    assert get_object("schemdraw.Drawing")
    assert get_object("schemdraw.svgconfig")


def test_get_object_nest():
    cache_clear()
    assert get_object("mkapi.items.Name.set_markdown")
    assert get_object("mkapi.items.Name")


def test_get_object_inherit():
    cache_clear()
    module = load_module("examples.styles.google")
    assert module
    cls = get_by_name(module.classes, "ExampleClass")
    assert isinstance(cls, Class)
    assert not get_by_name(cls.functions, "__init__")
    cache_clear()
    module = load_module("examples.styles")
    assert module
    cls = get_by_name(module.classes, "ExampleClass")
    assert isinstance(cls, Class)
    assert not get_by_name(cls.functions, "__init__")
