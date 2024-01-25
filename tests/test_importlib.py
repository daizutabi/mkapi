from mkapi.importlib import (
    get_object,
    get_source,
    iter_base_classes,
    load_module,
)
from mkapi.objects import Class, Function
from mkapi.utils import get_by_name


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
    assert cls.qualname == "MkAPIPlugin"
    assert cls.fullname == "mkapi.plugins.MkAPIPlugin"
    func = get_by_name(cls.functions, "on_config")
    assert func
    assert func.qualname == "MkAPIPlugin.on_config"
    assert func.fullname == "mkapi.plugins.MkAPIPlugin.on_config"
    base = next(iter_base_classes(cls))
    assert base.name == "BasePlugin"
    assert base.fullname == "mkdocs.plugins.BasePlugin"
    func = get_by_name(base.functions, "on_config")
    assert func
    assert func.qualname == "BasePlugin.on_config"
    assert func.fullname == "mkdocs.plugins.BasePlugin.on_config"
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    base = next(iter_base_classes(cls))
    assert base.name == "Config"
    assert base.qualname == "Config"
    assert base.fullname == "mkdocs.config.base.Config"


def test_inherit_base_classes():
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
    assert len(p) == 4
    assert p[0].name == "name"
    assert p[1].name == "type"
    assert p[2].name == "text"
    assert p[3].name == "items"
