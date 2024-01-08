from mkapi.objects import CACHE_MODULE, get_module, set_import_object


def test_import():
    module = get_module("mkapi.plugins")
    set_import_object(module)

    for x in module.imports:
        print(x.name, x.fullname, x.object)
    # assert 0
