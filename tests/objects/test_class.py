from mkapi.objects import Class, _inherit, _iter_base_classes, get_object, load_module
from mkapi.utils import get_by_name


def test_baseclasses():
    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    assert cls.qualname == "MkAPIPlugin"
    assert cls.fullname == "mkapi.plugins.MkAPIPlugin"
    func = cls.get_function("on_config")
    assert func
    assert func.qualname == "MkAPIPlugin.on_config"
    assert func.fullname == "mkapi.plugins.MkAPIPlugin.on_config"
    base = next(_iter_base_classes(cls))
    assert base.name == "BasePlugin"
    assert base.fullname == "mkdocs.plugins.BasePlugin"
    func = base.get_function("on_config")
    assert func
    assert func.qualname == "BasePlugin.on_config"
    assert func.fullname == "mkdocs.plugins.BasePlugin.on_config"
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    base = next(_iter_base_classes(cls))
    assert base.name == "Config"
    assert base.qualname == "Config"
    assert base.fullname == "mkdocs.config.base.Config"


def test_iter_bases():
    module = load_module("mkapi.objects")
    assert module
    cls = module.get_class("Class")
    assert cls
    cls.bases = list(_iter_base_classes(cls))
    bases = cls.iter_bases()
    assert next(bases).name == "Object"
    assert next(bases).name == "Class"


def test_inherit():
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    cls.bases = list(_iter_base_classes(cls))
    _inherit(cls, "attributes")
    assert cls.bases[0].fullname == "mkdocs.config.base.Config"
    assert get_by_name(cls.attributes, "config_file_path")
