from mkapi.core.module import get_module


def test_get_module():
    module = get_module("mkapi")
    assert module.parent is None
    assert module.object.markdown == "[mkapi](!mkapi)"
    assert "core" in module
    core = module.core
    assert core.parent is module
    assert core.object.markdown == "[mkapi](!mkapi).[core](!mkapi.core)"
    assert core.object.kind == "package"
    assert "base" in core
    base = core.base
    assert base.parent is core
    assert base.object.markdown == "[mkapi.core](!mkapi.core).[base](!mkapi.core.base)"
    assert base.object.kind == "module"
    assert len(base.objects) == 6
