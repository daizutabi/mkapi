import importlib
import inspect

from mkapi.modules import get_members, get_module, get_modulenames


def test_get_modulenames():
    names = list(get_modulenames("mkdocs.structure.files"))
    assert len(names) == 1
    names = list(get_modulenames("mkdocs"))
    module = None
    for name in names:
        module = importlib.import_module(name)
        assert module is not None
        sourcefile = inspect.getsourcefile(module)
        assert sourcefile is not None
    assert importlib.import_module(names[-1]) is module


def test_get_members():
    module = importlib.import_module("mkapi.modules")
    members = get_members(module)
    assert "get_module" in members
    assert "_walk" in members
    assert "TYPE_CHECKING" in members
    assert "annotations" in members


def test_members_id():
    module = importlib.import_module("mkapi.modules")
    a = get_members(module)
    module = importlib.import_module("mkapi.objects")
    b = get_members(module)
    assert a["annotations"] is b["annotations"]
    assert id(a["annotations"]) == id(b["annotations"])


def test_get_module():
    package = get_module("mkdocs")
    assert package.is_package()
    module = get_module("mkdocs.structure.files")
    assert not module.is_package()
    assert module.mtime > 1703851000
    assert module.path.stem == "files"
    assert module["Files"] is module.members["Files"]
