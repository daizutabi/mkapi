import pytest


def test_module_members_package_jinja():
    from mkapi.node import iter_module_members

    members = [m for m, _ in iter_module_members("jinja2")]
    assert "Template" in members
    assert "FileSystemLoader" in members
    assert "clear_caches" in members
    assert "Environment.compile" in members
    assert "ChoiceLoader.load" in members


def test_module_members_package_alias():
    from mkapi.node import iter_module_members

    members = [m for m, _ in iter_module_members("examples._styles")]
    assert "ExampleClassGoogle" in members
    assert "ExampleClassNumPy" in members
    assert "ExampleClassGoogle.readonly_property" in members
    assert "ExampleClassNumPy.readonly_property" in members


def test_module_members_overloads():
    from mkapi.node import _iter_module_members, iter_module_members

    members = [m for m, _ in _iter_module_members("mkapi.utils")]
    assert members.count("cache") > 1

    members = [m for m, _ in iter_module_members("mkapi.utils")]
    assert members.count("cache") == 1


def test_module_members_class():
    from mkapi.node import iter_module_members

    members = [m for m, _ in iter_module_members("mkapi.doc")]
    assert "Item.clone" in members
    assert "Section.clone" in members
    assert "Doc.clone" in members


@pytest.mark.parametrize("private", [True, False])
def test_module_members_private(private: bool):
    from mkapi.node import iter_module_members

    members = [m for m, _ in iter_module_members("mkapi.utils", private=private)]

    if private:
        assert any(m[0].startswith("_") for m in members)
    else:
        assert not any(m[0].startswith("_") for m in members)


@pytest.mark.parametrize("special", [True, False])
def test_module_members_special(special: bool):
    from mkapi.node import iter_module_members

    members = [m for m, _ in iter_module_members("mkapi.node", special=special)]

    if special:
        assert any("__" in m for m in members)
    else:
        assert not any("__" in m for m in members)


@pytest.mark.parametrize(
    "module",
    [
        "mkapi.node",
        "mkapi.object",
        "jinja2",
        "examples._styles.google",
        "examples._styles",
    ],
)
def test_module_members_have_objects(module: str):
    from mkapi.node import iter_module_members
    from mkapi.object import get_object

    members = iter_module_members(module, private=True, special=True)
    for m, _ in members:
        assert get_object(f"{module}.{m}") is not None


def test_iter_classes_from_module():
    from mkapi.node import iter_classes_from_module

    classes = list(iter_classes_from_module("mkapi.node"))
    assert len(classes) == 5
    assert "Node" in classes
    assert "Import" in classes
    assert "Definition" in classes
    assert "Assign" in classes
    assert "Module" in classes


def test_iter_classes_from_module_export():
    from mkapi.node import iter_classes_from_module

    classes = list(iter_classes_from_module("jinja2"))
    assert "Template" in classes
    assert "Environment" in classes


def test_iter_classes_from_module_alias():
    from mkapi.node import iter_classes_from_module

    classes = list(iter_classes_from_module("examples._styles"))
    assert len(classes) == 2
    assert "ExampleClassGoogle" in classes
    assert "ExampleClassNumPy" in classes


def test_iter_functions_from_module():
    from mkapi.node import iter_functions_from_module

    functions = list(iter_functions_from_module("mkapi.node"))
    assert "resolve" in functions
    assert "get_fullname_from_module" in functions


def test_iter_methods_from_class():
    from mkapi.node import iter_methods_from_class

    methods = list(iter_methods_from_class("MkApiPlugin", "mkapi.plugin"))
    assert "on_config" in methods
    assert "on_files" in methods
    assert "on_nav" in methods
    assert "on_page_markdown" in methods
    assert "on_page_content" in methods
    assert "__init__" not in methods


def test_iter_methods_from_class_property():
    from mkapi.node import iter_methods_from_class

    methods = list(iter_methods_from_class("Object", "mkapi.object"))
    assert not methods


def test_get_module_members():
    from mkapi.node import get_module_members, iter_module_members

    x = list(iter_module_members("examples"))
    y = get_module_members("examples")
    assert len(x) == len(y)
    assert x[0][0] == "mod_a"
    assert y[0][0] == "ClassA"
    assert y[1][0] == "ClassA.method_a"
    assert y[2][0] == "ClassB"
    assert y[3][0] == "ClassB.method_b"
    assert y[-2][0] == "mod_c_alias"
    assert y[-1][0] == "sub"
