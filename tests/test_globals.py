import ast
import inspect

from mkapi.globals import _resolve, get_globals
from mkapi.objects import create_module
from mkapi.utils import get_by_name


def test_resolve():
    assert _resolve("tqdm.tqdm") == "tqdm.std.tqdm"
    assert _resolve("logging.Template") == "string.Template"
    assert _resolve("halo.Halo") == "halo.halo.Halo"
    assert _resolve("jinja2.Template") == "jinja2.environment.Template"
    assert _resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert _resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert _resolve("mkdocs.config.Config") == "mkdocs.config.base.Config"


def test_relative_import():
    """# test module
    from .c import d
    from ..e import f
    """
    src = inspect.getdoc(test_relative_import)
    assert src
    node = ast.parse(src)
    module = create_module(node, "x.y.z")
    i = get_by_name(module.imports, "d")
    assert i
    assert i.fullname == "x.y.z.c.d"
    i = get_by_name(module.imports, "f")
    assert i
    assert i.fullname == "x.y.e.f"


def test_get_globals():
    x = get_globals("polars.dataframe.frame")
    print(x)
    # print(logging)
    # print(logging.re)
    # print(re._compiler)
    # print(re._compiler._parser)

    # print(logging.re.enum.sys)
    # print(logging.os)
    # print(logging.time)
    # assert 0

    # node = _i("import os, sys")
    # print(node)
    # assert 0
    # assert _get_fullname("sys") is None
    # assert _get_fullname("logging") == "logging"
    # assert _get_fullname("pathlib") == "pathlib"
    # assert _get_fullname("pathlib.Path") == "pathlib.Path"
    # assert _get_fullname("halo.Halo") == "halo.halo.Halo"
    # assert _get_fullname("mkdocs.config.MkDocsConfig") == "halo.halo.Halo"
    # assert 0

    # name = "polars.dataframe.frame"
    # node = get_module_node(name)
    # assert node
    # module = create_module(node, name)
    # assert module
    # for x in iter_imports(node, name):
    #     print(x.name, x.fullname)

    # from polars.dependencies import pandas

    # print(pandas)

    # assert 0

    # node = get_module_node(name)
    # assert node
    # module = create_module(node, name)
    # assert module
    # print(get_fullname(module, "MkDocsPage"))
    # print(get_fullname(module, "config_options.Type"))
    # assert 0

    # name = "mkdocs.config.config_options.Type"
    # assert get_fullname(module, "config_options.Type") == name
    # assert not get_fullname(module, "config_options.A")
    # module = load_module("mkdocs.plugins")
    # assert module
    # assert get_fullname(module, "jinja2") == "jinja2"
    # name = "jinja2.environment.Template"
    # assert get_fullname(module, "jinja2.Template") == name


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

# def test_iter_import_nodes_alias():
#     src = "import matplotlib.pyplot"
#     node = ast.parse(src).body[0]
#     assert isinstance(node, ast.Import)
#     x = list(_iter_imports_from_import(node))
#     assert len(x) == 2
#     assert x[0].fullname == "matplotlib"
#     assert x[1].fullname == "matplotlib.pyplot"
#     src = "import matplotlib.pyplot as plt"
#     node = ast.parse(src).body[0]
#     assert isinstance(node, ast.Import)
#     x = list(_iter_imports_from_import(node))
#     assert len(x) == 1
#     assert x[0].fullname == "matplotlib.pyplot"
#     assert x[0].name == "plt"
#     src = "from matplotlib import pyplot as plt"
#     node = ast.parse(src).body[0]
#     assert isinstance(node, ast.ImportFrom)
#     x = list(_iter_imports_from_import(node))
#     assert len(x) == 1
#     assert x[0].fullname == "matplotlib.pyplot"
#     assert x[0].name == "plt"
