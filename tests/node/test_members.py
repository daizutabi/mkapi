import pytest


def test_module_members_package():
    from mkapi.node import iter_module_members

    members = list(iter_module_members("examples.styles"))
    assert members == ["ExampleClassGoogle", "ExampleClassNumPy"]


def test_module_members_package_jinja():
    from mkapi.node import iter_module_members

    members = list(iter_module_members("jinja2"))
    assert "Template" in members
    assert "FileSystemLoader" in members
    assert "clear_caches" in members


def test_module_members_overloads():
    from mkapi.node import _iter_module_members, iter_module_members

    members = list(_iter_module_members("mkapi.utils"))
    assert members.count("cache") > 1

    members = list(iter_module_members("mkapi.utils"))
    assert members.count("cache") == 1


def test_module_members_class():
    from mkapi.node import iter_module_members

    members = list(iter_module_members("mkapi.doc"))
    assert "Item.clone" in members
    assert "Section.clone" in members
    assert "Doc.clone" in members


@pytest.mark.parametrize("private", [True, False])
def test_module_members_private(private: bool):
    from mkapi.node import iter_module_members

    members = list(iter_module_members("mkapi.utils", private=private))

    if private:
        assert any(m.startswith("_") for m in members)
    else:
        assert not any(m.startswith("_") for m in members)


@pytest.mark.parametrize("special", [True, False])
def test_module_members_special(special: bool):
    from mkapi.node import iter_module_members

    members = list(iter_module_members("mkapi.node", special=special))

    if special:
        assert any("__" in m for m in members)
    else:
        assert not any("__" in m for m in members)
