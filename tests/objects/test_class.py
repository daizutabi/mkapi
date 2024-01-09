from mkapi.objects import Class, _iter_base_classes, get_object


def test_baseclasses():
    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    base = next(_iter_base_classes(cls))
    assert base.name == "BasePlugin"
    assert base.get_fullname() == "mkdocs.plugins.BasePlugin"
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    base = next(_iter_base_classes(cls))
    assert base.name == "Config"
    assert base.get_fullname() == "mkdocs.config.base.Config"
