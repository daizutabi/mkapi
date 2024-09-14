"""Example package for testing MkAPI."""

import collections.abc  # noqa: F401
import os  # noqa: F401

import examples.mod_a
import examples.sub.mod_b
import examples.sub.subsub.mod_d

from .mod_a import ClassA, func_a
from .sub import mod_b
from .sub import mod_c as mod_c_alias
from .sub.mod_b import ClassB, func_b
from .sub.mod_c import ClassC as ClassCAlias
from .sub.mod_c import func_c as func_c_alias

__all__ = [
    "ClassA",
    "ClassB",
    "ClassCAlias",
    "examples",
    "func_a",
    "func_b",
    "func_c_alias",
    "mod_a",
    "mod_b",
    "mod_c_alias",
    "sub",
]
