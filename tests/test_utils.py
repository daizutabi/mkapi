from mkapi.utils import find_submodule_names


def test_find_submodule_names():
    names = find_submodule_names("mkdocs")
    assert "mkdocs.commands" in names
    assert "mkdocs.plugins" in names
