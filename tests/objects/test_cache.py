from mkapi.objects import CACHE_MODULE, CACHE_OBJECT, get_module, get_object


def test_cache():
    CACHE_MODULE.clear()
    CACHE_OBJECT.clear()
    module = get_module("mkapi.objects")
    c = get_object("mkapi.objects.Object")
    f = get_object("mkapi.objects.Module.get_class")
    assert c
    assert f
    assert c.get_module() is module
    assert f.get_module() is module


def test_get_module_check_mtime():
    m1 = get_module("mkdocs.structure.files")
    m2 = get_module("mkdocs.structure.files")
    assert m1 is m2
    CACHE_MODULE.clear()
    m3 = get_module("mkdocs.structure.files")
    m4 = get_module("mkdocs.structure.files")
    assert m2 is not m3
    assert m3 is m4
