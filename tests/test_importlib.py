import ast
import re

from mkapi.importlib import (
    LINK_PATTERN,
    _iter_texts,
    _iter_types,
    get_object,
    get_source,
    is_dataclass,
    iter_base_classes,
    load_module,
    modules,
)
from mkapi.objects import Class, Function, objects
from mkapi.utils import get_by_name


def test_module_not_found():
    assert load_module("xxx") is None
    assert modules["xxx"] is None
    assert load_module("markdown")
    assert "markdown" in modules


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


def test_module_kind():
    module = load_module("mkapi")
    assert module
    assert module.kind == "package"
    module = load_module("mkapi.objects")
    assert module
    assert module.kind == "module"


def test_get_object():
    modules.clear()
    objects.clear()
    module = load_module("mkapi.objects")
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
    modules.clear()
    m3 = load_module("mkdocs.structure.files")
    m4 = load_module("mkdocs.structure.files")
    assert m2 is not m3
    assert m3 is m4


def test_get_object_module():
    modules.clear()
    objects.clear()
    obj = get_object("mkapi.objects")
    module = load_module("mkapi.objects")
    assert obj is module


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
    assert is_dataclass(cls)
    p = cls.parameters
    assert len(p) == 4
    assert p[0].name == "name"
    assert p[1].name == "type"
    assert p[2].name == "text"
    assert p[3].name == "items"
