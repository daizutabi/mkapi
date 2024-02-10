import datetime
import sys
import time
from pathlib import Path

from mkapi.utils import (
    cache,
    cache_clear,
    cached_objects,
    find_submodule_names,
    get_module_node,
    get_module_node_source,
    get_module_path,
    is_module_cache_dirty,
    is_package,
    iter_submodule_names,
    module_cache,
)


@cache
def f():
    return datetime.datetime.now()  # noqa: DTZ005


c = cache({})


def test_cache():
    assert f in cached_objects
    x = f()
    time.sleep(0.1)
    y = f()
    assert x == y
    assert f.cache_info().currsize == 1
    cache_clear()
    assert f.cache_info().currsize == 0
    time.sleep(0.1)
    z = f()
    assert x != z
    assert f.cache_info().currsize == 1
    c[1] = 1
    cache_clear()
    assert not c


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


def test_get_module_node():
    node1 = get_module_node("mkapi")
    assert node1
    node2 = get_module_node("mkapi")
    assert node1 is node2


def test_module_cache(tmpdir: Path):
    module_cache.clear()
    assert not is_module_cache_dirty("a")

    sys.path.insert(0, str(tmpdir))

    path = tmpdir / "a.py"
    source = "1\n"
    with path.open("w") as f:
        f.write(source)
    get_module_path.cache_clear()
    path_ = get_module_path("a")
    assert path_
    assert is_module_cache_dirty("a")
    x = get_module_node_source("a")
    assert x
    assert x[1] == source
    assert "a" in module_cache
    assert not is_module_cache_dirty("a")
    y = get_module_node_source("a")
    assert y
    assert x[0] is y[0]
    time.sleep(0.01)
    source = "2\n"
    with path.open("w") as f:
        f.write(source)
    assert is_module_cache_dirty("a")

    sys.path.pop(0)
