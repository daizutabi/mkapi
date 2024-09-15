from __future__ import annotations

import collections.abc
from collections.abc import Generator
from dataclasses import dataclass


@dataclass
class DocstringAttribute:
    """class docstring

    Attributes:
        x (integer): attribute X
        y: attribute Y
    """

    x: int
    """attribute x"""

    y: int
    """attribute y"""

    z: int
    """attribute z

    second paragraph
    """


@dataclass
class PrivateAttribute:
    x: int
    """attribute x"""

    _y: int
    """private attribute y"""


def iterator(a: int) -> collections.abc.Iterator[int]:
    """iterator.

    Yields:
        the value of a.
    """
    yield a


def generator(a: int) -> Generator[list[PrivateAttribute], None, None]:
    """generator.

    Yields:
        the value of a.
    """
    yield [PrivateAttribute(x=a, _y=a)]
