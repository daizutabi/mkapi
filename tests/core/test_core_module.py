from mkapi.core.module import get_members, get_module, modules


def test_get_module():
    module = get_module("mkapi")
    assert module.parent is None
    assert module.object.markdown == "[mkapi](!mkapi)"
    assert "core" in module
    core = module["core"]
    assert core.parent is module
    assert core.object.markdown == "[mkapi](!mkapi).[core](!mkapi.core)"
    assert core.object.kind == "package"
    assert "base" in core
    base = core["base"]
    assert base.parent is core
    assert base.object.markdown == "[mkapi.core](!mkapi.core).[base](!mkapi.core.base)"
    assert base.object.kind == "module"
    assert len(base.node.members) == 6


def test_repr():
    module = get_module("mkapi.core.base")
    s = "Module('mkapi.core.base', num_sections=2, num_members=0)"
    assert repr(module) == s


def test_get_members():
    from mkapi import theme

    assert get_members(theme) == []


def test_get_module_from_object():
    from mkapi.core import base

    assert get_module(base).obj is base


def test_cache():
    assert 'mkapi.core.base' in modules
    assert 'mkapi.core.code' in modules
    assert 'mkapi.core.docstring' in modules
