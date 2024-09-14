import inspect

from mkapi.node import iter_module_members, parse_module
from mkapi.object import get_object
from mkapi.utils import list_exported_names


def test_parse_module_mkapi():
    assert not parse_module("mkapi")


def test_iter_module_members_mkapi():
    assert not list(iter_module_members("mkapi"))


def test_list_exported_names():
    names = list_exported_names("examples")
    assert "examples" in names
    assert "ClassA" in names
    assert "sub" in names


def test_parse_module():
    import examples

    for name, _ in parse_module("examples"):
        if "." not in name:
            assert getattr(examples, name)
        else:
            assert eval(f"examples.{name}")


def test_parse_module_names():
    names = [name for name, _ in parse_module("examples")]
    print(names)
    assert "ClassA" in names
    assert "ClassB" in names
    assert "ClassCAlias" in names
    assert "collections" in names
    assert "collections.abc" in names
    assert "examples" in names
    assert "examples.mod_a" in names
    assert "examples.sub" in names
    assert "examples.sub.mod_b" in names
    assert "func_a" in names
    assert "func_b" in names
    assert "func_c_alias" in names
    assert "mod_a" not in names
    assert "mod_b" in names
    assert "mod_c_alias" in names
    assert "os" in names
    assert "sub" not in names


def test_iter_module_members_inspect():
    import examples

    members = [name for name, _ in inspect.getmembers(examples)]
    for name, _ in iter_module_members("examples", child_only=True):
        assert name in members


def test_iter_module_members_names():
    names = [name for name, _ in iter_module_members("examples")]
    assert "ClassA" in names
    assert "ClassA.method_a" in names
    assert "ClassB" in names
    assert "ClassB.method_b" in names
    assert "ClassCAlias" in names
    assert "ClassCAlias.method_c" in names
    assert "collections" not in names
    assert "collections.abc" not in names
    assert "examples" not in names
    assert "examples.mod_a" not in names
    assert "examples.sub" not in names
    assert "examples.sub.mod_b" not in names
    assert "func_a" in names
    assert "func_a.func_a_inner" not in names
    assert "func_b" in names
    assert "func_c_alias" in names
    assert "mod_a" in names
    assert "mod_b" in names
    assert "mod_c_alias" in names
    assert "os" not in names
    assert "sub" in names


def test_iter_module_members_get_object():
    for name, _ in iter_module_members("examples"):
        assert get_object(name, "examples")
