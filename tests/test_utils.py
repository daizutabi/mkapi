import datetime
import importlib
import sys
import time
from collections import namedtuple
from pathlib import Path


def test_cache():
    from mkapi.utils import cache, cache_clear, cached_objects

    @cache
    def f():
        return datetime.datetime.now()  # noqa: DTZ005

    c = cache({})

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
    from mkapi.utils import get_module_path

    assert get_module_path("mkdocs")
    assert get_module_path("polars")
    assert get_module_path("sys") is None
    assert get_module_path("a.b") is None


def test_is_module():
    from mkapi.utils import _is_module, get_module_path

    path = get_module_path("mkapi.objects")
    assert path
    assert not _is_module(path, r"^mkapi\..+")


def test_is_package():
    from mkapi.utils import is_package

    assert is_package("mkdocs")
    assert is_package("mkapi")
    assert not is_package("mkapi.objects")
    assert not is_package("sys")
    assert not is_package("a.b")


def test_iter_submodule_names():
    from mkapi.utils import iter_submodule_names

    for name in iter_submodule_names("mkdocs"):
        assert name.startswith("mkdocs.")
    for name in iter_submodule_names("mkdocs.structure"):
        assert name.startswith("mkdocs.structure")
    assert not list(iter_submodule_names("sys"))


def test_find_submodule_names():
    from mkapi.utils import find_submodule_names, is_package

    names = find_submodule_names("mkdocs", lambda x: "tests" not in x)
    assert "mkdocs.plugins" in names
    assert "mkdocs.tests" not in names
    names = find_submodule_names("mkdocs", is_package)
    assert "mkdocs.structure" in names
    assert "mkdocs.plugins" not in names


def test_get_module_node():
    from mkapi.utils import get_module_node

    node1 = get_module_node("mkapi")
    assert node1
    node2 = get_module_node("mkapi")
    assert node1 is node2
    assert not get_module_node("sys")


def test_module_cache(tmpdir: Path):
    from mkapi.utils import (
        get_module_node_source,
        get_module_path,
        is_module_cache_dirty,
        module_cache,
    )

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
    from mkapi.utils import get_by_name

    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    a = get_by_name(x, "a")
    assert a
    assert a.value == 1
    assert not get_by_name(x, "d")


def test_get_by_kind():
    from mkapi.utils import get_by_kind

    A = namedtuple("A", ["kind", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    a = get_by_kind(x, "a")
    assert a
    assert a.value == 1
    assert not get_by_kind(x, "d")


def test_get_by_type():
    from mkapi.utils import get_by_type

    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    B = namedtuple("B", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), B("b", 3), B("c", 4)]
    a = get_by_type(x, B)
    assert a
    assert a.value == 3
    assert not get_by_type(x, int)


def test_del_by_name():
    from mkapi.utils import del_by_name, get_by_name

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


def test_unique_names():
    from mkapi.utils import unique_names

    A = namedtuple("A", ["name", "value"])  # noqa: PYI024
    x = [A("a", 1), A("a", 2), A("b", 3), A("c", 4)]
    y = [A("b", 1), A("a", 2), A("d", 3), A("e", 4)]
    assert unique_names(x, y) == ["a", "a", "b", "c", "d", "e"]


def test_iter_identifiers():
    from mkapi.utils import iter_identifiers

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


def test_get_module_name():
    from mkapi.utils import get_module_name

    name = "_collections_abc"
    abc = importlib.import_module(name)
    assert abc.__name__ == "collections.abc"
    assert get_module_name(name) == "collections.abc"


def test_get_object():
    from mkapi.utils import get_object_from_module

    name = "ExampleClass"
    module = "examples.styles.google"
    obj = get_object_from_module(name, module)
    assert obj.__name__ == name  # type: ignore
    assert obj.__module__ == module
    name_ = "ExampleClassGoogle"
    module_ = "examples.styles"
    obj = get_object_from_module(name_, module_)
    assert obj.__name__ == name  # type: ignore
    assert obj.__module__ == module


def test_get_export_names():
    from mkapi.utils import get_export_names

    x = get_export_names("tqdm")
    assert "tqdm" in x
    assert "trange" in x


def test_get_base_classes():
    from mkapi.utils import get_base_classes

    x = get_base_classes("Class", "mkapi.objects")
    assert x == [("Callable", "mkapi.objects")]


def test_split_name():
    from mkapi.utils import split_name

    x = split_name("ast")
    assert x
    assert x[0] == "ast"
    assert not x[1]

    x = split_name("mkapi.objects.ast")
    assert x
    assert x[0] == "ast"
    assert x[1] == "mkapi.objects"

    x = split_name("ast.ClassDef")
    assert x
    assert x[0] == "ClassDef"
    assert x[1] == "ast"

    x = split_name("examples.styles.google.ExampleClass")
    assert x
    assert x[0] == "ExampleClass"
    assert x[1] == "examples.styles.google"

    x = split_name("examples.styles.ExampleClassGoogle")
    assert x
    assert x[0] == "ExampleClassGoogle"
    assert x[1] == "examples.styles"
    assert not split_name("x.x")
