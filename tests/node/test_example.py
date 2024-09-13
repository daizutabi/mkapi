import example

from mkapi.node import iter_module_members, parse_module


def test_parse_module_mkapi():
    assert not parse_module("mkapi")


def test_iter_module_members_mkapi():
    assert not list(iter_module_members("mkapi"))


def test_parse_module():
    for name, _ in parse_module("example"):
        if "." not in name:
            assert getattr(example, name)
        else:
            assert name.startswith("example.")
            assert eval(name)


def test_iter_module_members():
    for name, _ in iter_module_members("example"):
        assert eval(f"example.{name}")
