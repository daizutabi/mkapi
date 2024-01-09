from mkapi.objects import (
    Class,
    _iter_base_classes,
    _postprocess_module,
    get_module,
    get_object,
)


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


# def test_signature():
#     module = get_module("mkapi.objects")
#     assert module
#     _postprocess_module(module)
#     cls = module.get_class("Class")
#     assert cls
#     for p in cls.parameters:
#         print(p, p.type)
#     assert 0
