import pytest


def test_resolve_module():
    from mkapi.node import resolve

    x = resolve("examples._styles.google")
    assert x == ("examples._styles.google", None)


def test_resolve_class():
    from mkapi.node import resolve

    x = resolve("examples._styles.google.ExampleClass")
    assert x == ("ExampleClass", "examples._styles.google")


def test_resolve_asname():
    from mkapi.node import resolve

    x = resolve("examples._styles.ExampleClassGoogle")
    assert x == ("ExampleClass", "examples._styles.google")


def test_resolve_attribute():
    from mkapi.node import resolve

    assert not resolve("examples._styles.ExampleClassGoogle.attr1")


def test_resolve_unknown():
    from mkapi.node import resolve

    assert not resolve("examples._styles.ExampleClassGoogle.attrX")


def test_resolve_none():
    from mkapi.node import resolve

    assert not resolve("x")


def test_resolve_jinja2():
    from mkapi.node import resolve

    x = resolve("jinja2.Template")
    assert x == ("Template", "jinja2.environment")


def test_resolve_mkdocs():
    from mkapi.node import resolve

    x = resolve("mkdocs.config.Config")
    assert x == ("Config", "mkdocs.config.base")


def test_resolve_mkapi():
    from mkapi.node import resolve

    x = resolve("mkapi.object.ast")
    assert x == ("ast", None)


def test_resolve_mkapi_class():
    from mkapi.node import resolve

    x = resolve("mkapi.object.ast.ClassDef")
    assert x == ("ClassDef", "ast")


def test_resolve_mkapi_module_plugin():
    from mkapi.node import resolve

    module = "mkapi.plugin"
    x = resolve("MkApiPlugin", module)
    assert x == ("MkApiPlugin", module)
    x = resolve("MkDocsConfig", module)
    assert x == ("MkDocsConfig", "mkdocs.config.defaults")


def test_resolve_mkapi_module_config():
    import mkapi.config
    from mkapi.node import resolve

    module = "mkapi.config"
    x = resolve("Config", module)
    assert x == ("Config", "mkdocs.config.base")
    x = resolve("config_options", module)
    assert x == ("mkdocs.config.config_options", None)
    assert x
    assert x[0] == mkapi.config.config_options.__name__


@pytest.mark.parametrize(
    "name", ["mkapi", "mkapi.ast", "mkapi.ast.AST", "mkapi.ast.XXX"]
)
def test_get_fullname_module(name):
    from mkapi.node import get_fullname_from_module

    x = get_fullname_from_module(name, "mkapi.node")
    if "AST" in name:
        assert x == "ast.AST"
    elif "XXX" in name:
        assert not x
    else:
        assert x == name


def test_get_fullname_class():
    from mkapi.node import get_fullname_from_module

    x = get_fullname_from_module("Class", "mkapi.object")
    assert x == "mkapi.object.Class"
    assert get_fullname_from_module("ast", "mkapi.object") == "ast"
    x = get_fullname_from_module("ast.ClassDef", "mkapi.object")
    assert x == "ast.ClassDef"


def test_get_fullname_jinja2():
    from mkapi.node import get_fullname_from_module

    x = get_fullname_from_module("jinja2.Template", "mkdocs.plugins")
    assert x == "jinja2.environment.Template"


@pytest.fixture(params=["", "._private", ".readonly_property"])
def attr(request):
    return request.param


def test_get_fullname_qualname(attr):
    from mkapi.node import get_fullname_from_module

    module = "examples._styles.google"
    name = f"ExampleClass{attr}"
    assert get_fullname_from_module(name, module) == f"{module}.{name}"


def test_get_fullname_qualname_alias(attr):
    from mkapi.node import get_fullname_from_module

    module = "examples._styles"
    name = f"ExampleClassGoogle{attr}"
    x = get_fullname_from_module(name, module)
    assert x == f"{module}.google.{name}".replace("Google", "")


def test_get_fullname_self():
    from mkapi.node import get_fullname_from_module

    name = "MkApiPlugin"
    module = "mkapi.plugin"
    assert get_fullname_from_module(name, module) == f"{module}.{name}"


def test_get_fullname_unknown():
    from mkapi.node import get_fullname_from_module

    assert not get_fullname_from_module("xxx", "mkapi.plugin")
    assert not get_fullname_from_module("jinja2.unknown", "mkdocs.plugins")


def test_get_fullname_plugin():
    from mkapi.node import get_fullname_from_module

    module = "mkapi.plugin"
    x = get_fullname_from_module("MkDocsConfig", module)
    assert x == "mkdocs.config.defaults.MkDocsConfig"
    x = get_fullname_from_module("get_plugin_logger", module)
    assert x == "mkdocs.plugins.get_plugin_logger"


def test_get_fullname_config():
    from mkapi.node import get_fullname_from_module

    module = "mkapi.config"
    x = get_fullname_from_module("Config", module)
    assert x == "mkdocs.config.base.Config"
    x = get_fullname_from_module("config_options", module)
    assert x == "mkdocs.config.config_options"
    x = get_fullname_from_module("config_options.Type", module)
    assert x == "mkdocs.config.config_options.Type"


def test_get_fullname_nested():
    from mkapi.node import get_fullname_from_module

    assert get_fullname_from_module("mkapi.doc.Item.name") == "mkapi.doc.Item.name"
    assert not get_fullname_from_module("mkapi.doc.Item.mkapi")


def test_get_fullname_method():
    from mkapi.node import get_fullname_from_module

    assert get_fullname_from_module("mkapi.doc.Item.clone") == "mkapi.doc.Item.clone"
    assert get_fullname_from_module("Item.clone", "mkapi.doc") == "mkapi.doc.Item.clone"
    assert get_fullname_from_module("Item", "mkapi.parser") == "mkapi.doc.Item"
    assert (
        get_fullname_from_module("Item.clone", "mkapi.parser") == "mkapi.doc.Item.clone"
    )
