from mkapi.objects import (
    Class,
    Function,
    create_module,
    resolve,
    resolve_from_module,
)


def test_resolve_examples():
    name = "examples.styles.google"
    x = resolve(name)
    assert x
    assert x[0] == name
    assert x[1] is None
    name = "examples.styles.google.ExampleClass"
    x = resolve(name)
    assert x
    assert x[0] == "ExampleClass"
    assert x[1] == "examples.styles.google"
    name = "examples.styles.ExampleClassGoogle"
    x = resolve(name)
    assert x
    assert x[0] == "ExampleClassGoogle"
    assert x[1] == "examples.styles"
    name = "examples.styles.ExampleClassGoogle.attr1"
    x = resolve(name)
    assert x
    assert x[0] == "ExampleClassGoogle.attr1"
    assert x[1] == "examples.styles"
    assert not resolve("x")
    assert not resolve("examples.styles.X")
    assert not resolve("examples.styles.ExampleClassGoogle.attrX")


def test_resolve_tqdm():
    x = resolve("tqdm.tqdm")
    assert x
    assert x[0] == "tqdm"
    assert x[1] == "tqdm"
    assert x[2].fullname == "tqdm.std.tqdm"


def test_resolve_jinja2():
    x = resolve("jinja2.Template")
    assert x
    assert x[0] == "Template"
    assert x[1] == "jinja2"
    assert x[2].fullname == "jinja2.environment.Template"


def test_resolve_mkdocs():
    x = resolve("mkdocs.config.Config")
    assert x
    assert x[0] == "Config"
    assert x[1] == "mkdocs.config"
    assert x[2].fullname == "mkdocs.config.base.Config"


def test_resolve_mkapi():
    x = resolve("mkapi.objects.ast")
    assert x
    assert x[0] == "ast"
    assert x[1] == "mkapi.objects"
    assert x[2].fullname == "ast"

    assert not resolve("mkapi.objects.ast.ClassDef")


def test_resolve_from_module():
    x = resolve_from_module("Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"
    x = resolve_from_module("mkapi.objects", "mkapi.objects")
    assert x == "mkapi.objects"
    x = resolve_from_module("mkapi.objects.Class", "mkapi.objects")
    assert x == "mkapi.objects.Class"

    assert resolve_from_module("ast", "mkapi.objects") == "ast"
    x = resolve_from_module("ast.ClassDef", "mkapi.objects")
    assert x == "ast.ClassDef"

    x = resolve_from_module("jinja2.Template", "mkdocs.plugins")
    assert x == "jinja2.Template"
    y = resolve(x)
    assert y
    assert y[2].fullname == "jinja2.environment.Template"
    x = resolve_from_module("jinja2.XXX", "mkdocs.plugins")
    assert x == "jinja2.XXX"
    assert not resolve(x)

    for x in ["mkapi", "mkapi.ast", "mkapi.ast.XXX"]:
        y = resolve_from_module(x, "mkapi.nodes")
        assert x == y


def test_resolve_from_module_qualname():
    module = "examples.styles.google"
    name = "ExampleClass"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    name = "ExampleClass.attr1"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    name = "ExampleClass.readonly_property"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    name = "ExampleClass._private"
    assert resolve_from_module(name, module) == f"{module}.{name}"
    module = "examples.styles"
    name = "ExampleClassGoogle"
    x = resolve_from_module(name, module)
    assert x == "examples.styles.ExampleClassGoogle"
    name = "ExampleClassGoogle.readwrite_property"
    x = resolve_from_module(name, module)
    assert x == "examples.styles.ExampleClassGoogle.readwrite_property"
