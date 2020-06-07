from mkapi.core.module import get_module


def test_get_module():
    module = get_module("mkapi")
    assert module.parent is None
    assert module.markdown == "[mkapi](!mkapi)"
    assert "core" in module
    core = module.core
    assert core.parent is module
    assert core.markdown == "[mkapi](!mkapi).[core](!mkapi.core)"
    assert core.kind == "package"
    assert "base" in core
    base = core.base
    assert base.parent is core
    assert base.markdown == "[mkapi.core](!mkapi.core).[base](!mkapi.core.base)"
    assert base.kind == "module"
    assert len(base.objects) == 5
    base.objects
