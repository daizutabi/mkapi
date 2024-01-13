import ast

import pytest

import mkapi.ast
import mkapi.objects
from mkapi.objects import (
    Class,
    Function,
    Module,
    get_module_path,
    get_object,
    load_module,
    modules,
    objects,
)


@pytest.fixture(scope="module")
def module():
    path = get_module_path("mkdocs.structure.files")
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


def test_not_found():
    assert load_module("xxx") is None
    assert mkapi.objects.modules["xxx"] is None
    assert load_module("markdown")
    assert "markdown" in mkapi.objects.modules


def test_repr():
    module = load_module("mkapi")
    assert repr(module) == "Module(mkapi)"
    module = load_module("mkapi.objects")
    assert repr(module) == "Module(mkapi.objects)"
    obj = get_object("mkapi.objects.Object")
    assert repr(obj) == "Class(Object)"


def test_load_module_source():
    module = load_module("mkdocs.structure.files")
    assert module
    assert module.source
    assert "class File" in module.source
    module = load_module("mkapi.plugins")
    assert module
    cls = module.get_class("MkAPIConfig")
    assert cls
    assert cls.module is module
    src = cls.get_source()
    assert src
    assert src.startswith("class MkAPIConfig")
    src = module.get_source()
    assert src
    assert "MkAPIPlugin" in src


def test_load_module_from_object():
    module = load_module("mkdocs.structure.files")
    assert module
    c = module.classes[1]
    m = c.module
    assert module is m


def test_fullname(google: Module):
    c = google.get_class("ExampleClass")
    assert isinstance(c, Class)
    f = c.get_function("example_method")
    assert isinstance(f, Function)
    assert c.fullname == "examples.styles.example_google.ExampleClass"
    name = "examples.styles.example_google.ExampleClass.example_method"
    assert f.fullname == name


def test_cache():
    modules.clear()
    objects.clear()
    module = load_module("mkapi.objects")
    c = get_object("mkapi.objects.Object")
    f = get_object("mkapi.objects.Module.get_class")
    assert isinstance(c, Class)
    assert c.module is module
    assert isinstance(f, Function)
    assert f.module is module
    c2 = get_object("mkapi.objects.Object")
    f2 = get_object("mkapi.objects.Module.get_class")
    assert c is c2
    assert f is f2
    m1 = load_module("mkdocs.structure.files")
    m2 = load_module("mkdocs.structure.files")
    assert m1 is m2
    modules.clear()
    m3 = load_module("mkdocs.structure.files")
    m4 = load_module("mkdocs.structure.files")
    assert m2 is not m3
    assert m3 is m4


def test_module_kind():
    module = load_module("mkapi")
    assert module
    assert module.kind == "package"
    module = load_module("mkapi.objects")
    assert module
    assert module.kind == "module"


def test_get_fullname_with_attr():
    module = load_module("mkapi.plugins")
    assert module
    name = module.get_fullname("config_options.Type")
    assert name == "mkdocs.config.config_options.Type"
    assert not module.get_fullname("config_options.A")
