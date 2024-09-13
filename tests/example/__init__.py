"""Example package for testing MkAPI."""

import example.mod_a
import example.sub.mod_b

from .mod_a import ClassA, func_a
from .sub import mod_b
from .sub import mod_c as mod_c_alias
from .sub.mod_b import ClassB, func_b
from .sub.mod_c import ClassC as ClassC_alias
from .sub.mod_c import func_c as func_c_alias

# __all__ = [
#     "ClassA",
#     "ClassB",
#     "ClassC_alias",
#     "func_a",
#     "func_b",
#     "func_c_alias",
#     "example",
#     "mod_a",
#     "sub",
#     "mod_b",
#     "mod_c_alias",
# ]
