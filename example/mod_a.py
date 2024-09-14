"""Module A."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .sub.mod_b import ClassB


class ClassA:
    """Class A."""

    attr_a: str = "string"
    """Attribute A."""

    def method_a(self, x: Iterable[str], y: ClassB) -> ClassA:
        """Method A. Return `ClassA`.

        Args:
            x: An iterable of strings.
            y: An instance of `ClassB`.

        Returns:
            An instance of `ClassA`.
        """
        if not x:
            raise ValueError

        return self


def func_a(x: int) -> int:
    """Function A.

    Args:
        x: An integer.

    Returns:
        An integer.

    See Also:
        - `ClassA.method_a`
        - [`func_b`][example.sub.mod_b.func_b]
    """
    return 2 * x
