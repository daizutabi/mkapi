from mkapi.objects import (
    CACHE_MODULE,
    CACHE_MODULE_NODE,
    CACHE_OBJECT,
    get_module,
    get_object,
)


def test_cache():
    CACHE_MODULE.clear()
    CACHE_MODULE_NODE.clear()
    CACHE_OBJECT.clear()
    module = get_module("mkapi.objects")
    c = get_object("mkapi.objects.Object")
    f = get_object("mkapi.objects.Module.get_class")
    assert c
    assert f
    assert c.get_module() is module
    assert f.get_module() is module
