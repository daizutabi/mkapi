from mkapi.items import Import, iter_imports
from mkapi.objects import Module, create_module
from mkapi.utils import get_by_name, get_module_node, get_module_path

# def get_fullname(import_: Import) -> str | None:
#     if get_module_path(import_.fullname):
#         return import_.fullname
#     if "." not in import_.fullname:
#         return None
#     module, name = import_.fullname.rsplit(".", maxsplit=1)
#     if not (node := get_module_node(module)):
#         return None
#     if i := get_by_name(iter_imports(node, module), name):
#         return get_fullname(i)
#     return import_.fullname


# def iter_import_fullnames(module: Module):
#     for import_ in iter_imports(module.node, module.name):
#         yield import_.name, get_fullname(import_)


def test_imports():
    name = "mkapi.plugins"
    node = get_module_node(name)
    assert node
    # module = create_module(node, name)
    # assert module
    for x in iter_imports(node, name):
        print(x.name, x.fullname)

    assert 0


# def test_get_fullname():
#     module = load_module("mkapi.plugins")
#     assert module
#     name = "MkDocsPage"
#     print(get_member(module, name))
#     import_ = get_by_name(module.imports, name)
#     print(get_fullname(module, name))

#     print(get_fullname(module, name))

#     name = "mkdocs.structure.pages.Page"
#     assert 0
# assert get_fullname(module, "MkDocsPage") == name
# name = "mkdocs.config.config_options.Type"
# assert get_fullname(module, "config_options.Type") == name
# assert not get_fullname(module, "config_options.A")
# module = load_module("mkdocs.plugins")
# assert module
# assert get_fullname(module, "jinja2") == "jinja2"
# name = "jinja2.environment.Template"
# assert get_fullname(module, "jinja2.Template") == name


# def test_get_fullname_self():
#     module = load_module("mkapi.objects")
#     assert module
#     assert get_fullname(module, "Object") == "mkapi.objects.Object"
#     assert get_fullname(module, "mkapi.objects") == "mkapi.objects"
#     assert get_fullname(module, "mkapi.objects.Object") == "mkapi.objects.Object"


# def test_fullname_polars():
#     module = load_module("polars.dataframe.frame")
#     assert module
#     im = get_member(module, "DataType")
#     assert im
#     assert isinstance(im, Import)
#     print(im.name, im.fullname)
#     module = load_module("polars")
#     assert module
#     obj = get_member(module, "DataType")
#     assert obj
#     print(obj.fullname, type(obj))
#     module = load_module("polars.datatypes")
#     assert module
#     obj = get_member(module, "DataType")
#     assert obj
#     print(obj.fullname, type(obj))
#     assert 0
