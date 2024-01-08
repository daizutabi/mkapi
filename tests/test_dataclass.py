import importlib
import inspect
import sys
import tempfile
from pathlib import Path

import pytest

from mkapi.dataclasses import (
    _get_dataclass_decorator,
    _iter_decorator_args,
    is_dataclass,
)
from mkapi.objects import _get_module_from_source, get_module

source = """
import dataclasses
from dataclasses import dataclass, field
@f()
@dataclasses.dataclass
@g
class A:
    pass
@dataclass(init=True,repr=False)
class B:
    x: list[A]=field(init=False)
    y: int
    z: str=field()
"""


def test_decorator_arg():
    module = _get_module_from_source(source)
    cls = module.get_class("A")
    assert cls
    assert is_dataclass(cls, module)
    deco = _get_dataclass_decorator(cls, module)
    assert deco
    assert not list(_iter_decorator_args(deco))
    cls = module.get_class("B")
    assert cls
    assert is_dataclass(cls, module)
    deco = _get_dataclass_decorator(cls, module)
    assert deco
    deco_dict = dict(_iter_decorator_args(deco))
    assert deco_dict["init"]
    assert not deco_dict["repr"]


@pytest.fixture()
def path():
    path = Path(tempfile.NamedTemporaryFile(suffix=".py", delete=False).name)
    sys.path.insert(0, str(path.parent))
    yield path
    del sys.path[0]
    path.unlink()


@pytest.fixture()
def load(path: Path):
    def load(source: str):
        with path.open("w") as f:
            f.write(source)
        module = importlib.import_module(path.stem)
        cls = dict(inspect.getmembers(module))["C"]
        params = inspect.signature(cls).parameters
        module = get_module(path.stem)
        assert module
        cls = module.get_class("C")
        assert cls
        return cls.parameters, params

    return load
