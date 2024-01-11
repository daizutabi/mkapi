# from mkapi.objects import (
#     Attribute,
#     Class,
#     Function,
#     Import,
#     Module,
#     load_module,
#     set_import_object,
# )


# def test_import():
#     module = load_module("mkapi.plugins")
#     assert module
#     set_import_object(module)

#     i = module.get("annotations")
#     assert isinstance(i, Import)
#     assert isinstance(i.object, Attribute)
#     i = module.get("importlib")
#     assert isinstance(i, Import)
#     assert isinstance(i.object, Module)
#     i = module.get("Path")
#     assert isinstance(i, Import)
#     assert isinstance(i.object, Class)
#     i = module.get("get_files")
#     assert isinstance(i, Import)
#     assert isinstance(i.object, Function)


# for x in module.imports:
#     print(x.name, x.fullname, x.object)
