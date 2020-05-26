"""Module level docstring."""
from dataclasses import dataclass, field
from typing import Iterator, List, Tuple


def add(x: int, y: int = 1) -> int:
    """Returns $x + y$.

    Args:
        x: The first parameter.
        y: The second parameter. Default={default}.

    Returns:
        Added value.

    Examples:
        >>> add(1, 2)
        3

    !!! note
        You can use the [admonition extension of
        MkDocs](https://squidfunk.github.io/mkdocs-material/extensions/admonition/).

    Note:
        But you should use `Note` section instead for consistency.
    """
    return x + y


def gen(n) -> Iterator[str]:
    """Yields a numbered string.

    Args:
        n (int): The length of iteration.

    Yields:
       A numbered string.
    """
    for x in range(n):
        yield f"a{x}"


class ExampleClass:
    def __init__(self, x: List[int], y: Tuple[str, int]):
        """A normal class.

        Args:
            x: The first parameter.
            y: The second parameter.

        Attributes:
            z (str): The first attribute.

        Raises:
            ValueError: If the length of `x` is equal to 0.
        """
        if len(x) == 0:
            raise ValueError()
        self.z = "abc"

    def message(self, n: int) -> List[str]:
        """Returns a message list.

        Args:
            n: Repeatation.
        """
        return [self.z] * n

    @property
    def readonly_property(self):
        """str: Read-only property documentation."""
        return "readonly_property"

    @property
    def readwrite_property(self) -> List[int]:
        """Read-write property documentation."""
        return [1, 2, 3]

    @readwrite_property.setter
    def readwrite_property(self, value):
        """Docstring in setter is ignored."""


@dataclass
class ExampleDataClass:
    """A dataclass.

    Args:
        x: The first parameter.

    Attributes:
        x: The first attribute.
        y: The second attribute.
    """

    x: int = 0
    y: int = field(default=1, init=False)
