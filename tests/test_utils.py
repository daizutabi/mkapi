from mkapi.utils import (
    find_submodulenames,
    is_package,
    iter_submodulenames,
)


def test_is_package():
    assert is_package("mkdocs")
    assert is_package("mkapi")
    assert not is_package("mkapi.objects")


def test_iter_submodulenames():
    for name in iter_submodulenames("mkdocs"):
        assert name.startswith("mkdocs.")
    for name in iter_submodulenames("mkdocs.structure"):
        assert name.startswith("mkdocs.structure")


def test_find_submodulenames():
    names = find_submodulenames("mkdocs", lambda x: "tests" not in x)
    assert "mkdocs.plugins" in names
    assert "mkdocs.tests" not in names
    names = find_submodulenames("mkdocs", is_package)
    assert "mkdocs.structure" in names
    assert "mkdocs.plugins" not in names
