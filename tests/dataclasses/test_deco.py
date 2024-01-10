from mkapi.dataclasses import (
    _get_dataclass_decorator,
    _iter_decorator_args,
    is_dataclass,
)
from mkapi.objects import get_module_from_source

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
    module = get_module_from_source(source)
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