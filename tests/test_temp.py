from mkapi.importlib import get_fullname, load_module
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
