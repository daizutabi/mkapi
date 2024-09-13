"""A subpackage"""

# import examples.subpackage.module2
from examples import _styles
from examples.subpackage import module as M
from examples.subpackage.module import A

__all__ = ["_styles", "M", "A"]
