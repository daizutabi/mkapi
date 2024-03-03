import pytest


def test_resolve_module():
    from mkapi.nodes import resolve

    x = resolve("examples.styles.google")
    assert x == ("examples.styles.google", None)


def test_resolve_class():
    from mkapi.nodes import resolve

    x = resolve("examples.styles.google.ExampleClass")
    assert x == ("ExampleClass", "examples.styles.google")


def test_resolve_alias():
    from mkapi.nodes import resolve

    x = resolve("examples.styles.ExampleClassGoogle")
    assert x == ("ExampleClass", "examples.styles.google")


def test_resolve_attribute():
    from mkapi.nodes import resolve

    x = resolve("examples.styles.ExampleClassGoogle.attr1")
    assert x == ("ExampleClass.attr1", "examples.styles.google")


def test_resolve_unknown():
    from mkapi.nodes import resolve

    x = resolve("examples.styles.ExampleClassGoogle.attrX")
    assert x == ("ExampleClass.attrX", "examples.styles.google")


def test_resolve_none():
    from mkapi.nodes import resolve

    assert not resolve("x")


def test_resolve_tqdm():
    from mkapi.nodes import resolve

    x = resolve("tqdm.tqdm")
    assert x == ("tqdm", "tqdm.std")


def test_resolve_jinja2():
    from mkapi.nodes import resolve

    x = resolve("jinja2.Template")
    assert x == ("Template", "jinja2.environment")


def test_resolve_mkdocs():
    from mkapi.nodes import resolve

    x = resolve("mkdocs.config.Config")
    assert x == ("Config", "mkdocs.config.base")


def test_resolve_mkapi():
    from mkapi.nodes import resolve

    x = resolve("mkapi.objects.ast")
    assert x == ("ast", None)


def test_resolve_mkapi_class():
    from mkapi.nodes import resolve

    x = resolve("mkapi.objects.ast.ClassDef")
    assert x == ("ClassDef", "ast")


def test_resolve_mkapi_module():
    import mkapi.plugins
    from mkapi.nodes import resolve

    module = "mkapi.plugins"
    x = resolve("MkAPIPlugin", module)
    assert x == ("MkAPIPlugin", module)
    x = resolve("MkDocsConfig", module)
    assert x == ("MkDocsConfig", "mkdocs.config.defaults")
    x = resolve("Config", module)
    assert x == ("Config", "mkdocs.config.base")
    x = resolve("config_options", module)
    assert x == ("mkdocs.config.config_options", None)
    assert x
    assert x[0] == mkapi.plugins.config_options.__name__


def test_resolve_polars():
    from mkapi.nodes import resolve

    x = resolve("polars.api")
    assert x
    assert x[0] == "polars.api"
    assert not x[1]


@pytest.mark.parametrize("name", ["mkapi", "mkapi.ast", "mkapi.ast.XXX"])
def test_get_fullname_module(name):
    from mkapi.nodes import get_fullname

    assert get_fullname(name, "mkapi.nodes") == name


def test_get_fullname_class():
    from mkapi.nodes import get_fullname

    x = get_fullname("Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"
    assert get_fullname("ast", "mkapi.objects") == "ast"
    x = get_fullname("ast.ClassDef", "mkapi.objects")
    assert x == "ast.ClassDef"


def test_get_fullname_jinja2():
    from mkapi.nodes import get_fullname

    x = get_fullname("jinja2.Template", "mkdocs.plugins")
    assert x == "jinja2.environment.Template"
    x = get_fullname("jinja2.XXX", "mkdocs.plugins")
    assert x == "jinja2.XXX"


@pytest.fixture(params=["", ".attr1", "._private", ".readonly_property"])
def attr(request):
    return request.param


def test_get_fullname_qualname(attr):
    from mkapi.nodes import get_fullname

    module = "examples.styles.google"
    name = f"ExampleClass{attr}"
    assert get_fullname(name, module) == f"{module}.{name}"


def test_get_fullname_qualname_alias(attr):
    from mkapi.nodes import get_fullname

    module = "examples.styles"
    name = f"ExampleClassGoogle{attr}"
    x = get_fullname(name, module)
    assert x == f"{module}.google.{name}".replace("Google", "")


def test_get_fullname_schemdraw():
    from mkapi.nodes import get_fullname

    x = get_fullname("Drawing", "schemdraw")
    assert x == "schemdraw.schemdraw.Drawing"


def test_get_fullname_self():
    from mkapi.nodes import get_fullname

    name = "MkAPIPlugin"
    module = "mkapi.plugins"
    assert get_fullname(name, module) == f"{module}.{name}"


def test_get_fullname_other():
    from mkapi.nodes import get_fullname

    module = "mkapi.plugins"
    x = get_fullname("MkDocsConfig", module)
    assert x == "mkdocs.config.defaults.MkDocsConfig"
    x = get_fullname("Config", module)
    assert x == "mkdocs.config.base.Config"
    x = get_fullname("config_options", module)
    assert x == "mkdocs.config.config_options"
    x = get_fullname("config_options.Type", module)
    assert x == "mkdocs.config.config_options.Type"
    x = get_fullname("get_plugin_logger", module)
    assert x == "mkdocs.plugins.get_plugin_logger"


def test_get_fullname_polars():
    from mkapi.nodes import get_fullname

    x = get_fullname("DataType", "polars.dataframe.frame")
    assert x == "polars.datatypes.classes.DataType"
    assert get_fullname("api", "polars") == "polars.api"
