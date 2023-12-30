from mkapi.modules import find_submodules, get_module


def test_get_module():
    module = get_module("mkdocs")
    assert module.is_package()
    assert len(find_submodules(module)) > 0
    module = get_module("mkdocs.structure.files")
    assert not module.is_package()
    assert not find_submodules(module)
    assert module.mtime > 1703851000
    assert module.path.stem == "files"
