from mkapi.objects import _postprocess_module, get_module


def test_signature():
    module = get_module("mkapi.objects")
    assert module
    _postprocess_module(module)
    cls = module.get_class("Class")
    assert cls
    for p in cls.parameters:
        print(p, p.type)
    # assert 0
