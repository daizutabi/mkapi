"""Module A."""

from .sub.mod_b import ClassB as ClassBAlias
from .sub.mod_c import ClassC, func_c

__all__ = ["ClassBAlias", "ClassC"]


class ClassA:
    """Class A."""

    def method_a(self):
        """Method A."""


def func_a():
    """Function A."""
    func_c()

    def func_a_inner():
        """Function A inner."""
