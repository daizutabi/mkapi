import datetime
import sys
import time
from collections import namedtuple
from pathlib import Path

from mkapi.items import Name
from mkapi.utils import (
    _is_module,
    cache,
    cache_clear,
    cached_objects,
    del_by_name,
    find_submodule_names,
    get_by_kind,
    get_by_name,
    get_by_type,
    get_module_node,
    get_module_node_source,
    get_module_path,
    is_module_cache_dirty,
    is_package,
    iter_by_name,
    iter_identifiers,
    iter_submodule_names,
    module_cache,
    unique_names,
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
    assert get_module_path("sys") is None
    assert get_module_path("a.b") is None


def test_is_module():
    path = get_module_path("mkapi.objects")
    assert path
    assert not _is_module(path, r"^mkapi\..+")


def test_is_package():
    assert is_package("mkdocs")
    assert is_package("mkapi")
    assert not is_package("mkapi.objects")
    assert not is_package("sys")
    assert not is_package("a.b")


def test_iter_submodule_names():
    for name in iter_submodule_names("mkdocs"):
        assert name.startswith("mkdocs.")
    for name in iter_submodule_names("mkdocs.structure"):
        assert name.startswith("mkdocs.structure")
    assert not list(iter_submodule_names("sys"))


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
    assert not get_module_node("sys")


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


def test_get_by_name():
    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    a = get_by_name(x, "a")
    assert a
    assert a.value == 1
    assert not get_by_name(x, "d")
    x = [A(Name("a"), 1), A(Name("a"), 2), A(Name("b"), 3), A(Name("c"), 4)]
    a = get_by_name(x, Name("a"))
    assert a
    assert a.value == 1
    assert not get_by_name(x, Name("d"))
    assert get_by_name(x, "b")
    assert not get_by_name(x, "e")


def test_get_by_kind():
    A = namedtuple("A", ["kind", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    a = get_by_kind(x, "a")
    assert a
    assert a.value == 1
    assert not get_by_kind(x, "d")


def test_get_by_type():
    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    B = namedtuple("B", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), B("b", 3), B("c", 4)]
    a = get_by_type(x, B)
    assert a
    assert a.value == 3
    assert not get_by_type(x, int)


def test_del_by_name():
    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    del_by_name(x, "a")
    assert len(x) == 3
    a = get_by_name(x, "a")
    assert a
    assert a.value == 2
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    del_by_name(x, "c")
    assert x == [A("a", 1), A("a", 2), A("b", 3)]
    x = [A(Name("a"), 1), A(Name("a"), 2), A(Name("b"), 3), A(Name("c"), 4)]
    assert get_by_name(x, Name("c"))
    del_by_name(x, Name("c"))
    assert not get_by_name(x, Name("c"))
    x = [A(Name("a"), 1), A(Name("a"), 2), A(Name("b"), 3), A(Name("c"), 4)]
    assert get_by_name(x, "c")
    del_by_name(x, "c")
    assert not get_by_name(x, "c")


def test_unique_names():
    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    y = [A("b", 1), A("a", 2), A("d", 3), A("e", 4)]
    assert unique_names(x, y) == ["a", "a", "b", "c", "d", "e"]


def test_iter_identifiers():
    x = "a, b, c"
    y = list(iter_identifiers(x))
    assert y[0] == ("a", True)
    assert y[3] == ("b", True)
    assert y[6] == ("c", True)
    x = "a.b[c], def(xyz)"
    y = list(iter_identifiers(x))
    assert y[0] == ("a.b", True)
    assert y[2] == ("c", True)
    assert y[6] == ("def", True)
    assert y[8] == ("xyz", True)
    x = "abc'def'"
    y = list(iter_identifiers(x))
    assert y == [("abc", True), ("'def'", False)]
    x = "abc."
    y = list(iter_identifiers(x))
    assert y == [("abc", True), (".", False)]
    x = "1"
    assert next(iter_identifiers(x)) == ("1", False)
    x = "a1"
    assert next(iter_identifiers(x)) == ("a1", True)
    x = "a,b"
    assert list(iter_identifiers(x)) == [("a", True), (",", False), ("b", True)]
    x = "dict, Sequence, ndarray, 'Series', or pandas.DataFrame."
    x = list(iter_identifiers(x))
    assert ("dict", True) in x
    assert ("Sequence", True) in x
    assert ("'Series'", False) in x
    assert ("pandas.DataFrame", True) in x
