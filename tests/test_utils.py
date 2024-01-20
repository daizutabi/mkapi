from mkapi.utils import (
    find_submodule_names,
    get_module_path,
    is_package,
    iter_submodule_names,
)


def test_get_module_path():
    assert get_module_path("mkdocs")
    assert get_module_path("polars")


def test_is_package():
    assert is_package("mkdocs")
    assert is_package("mkapi")
    assert not is_package("mkapi.objects")


def test_iter_submodule_names():
    for name in iter_submodule_names("mkdocs"):
        assert name.startswith("mkdocs.")
    for name in iter_submodule_names("mkdocs.structure"):
        assert name.startswith("mkdocs.structure")


def test_find_submodule_names():
    names = find_submodule_names("mkdocs", lambda x: "tests" not in x)
    assert "mkdocs.plugins" in names
    assert "mkdocs.tests" not in names
    names = find_submodule_names("mkdocs", is_package)
    assert "mkdocs.structure" in names
    assert "mkdocs.plugins" not in names
