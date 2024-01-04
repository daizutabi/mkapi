from __future__ import annotations

from dataclasses import dataclass
from typing import TypeGuard

from mkapi.objects import Class, Function, Import, Module, get_module


@dataclass(repr=False)
class Object:
    """Object class."""

    _obj: Module | Class | Function | Import

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._obj})"

    def ismodule(self) -> bool:
        return isinstance(self._obj, Module)


def get_object(name: str) -> Object:
    if module := get_module(name):
        x = Object(module)
