"""Module level docstring."""
from collections.abc import Iterator
from dataclasses import dataclass, field

#: The first module level attribute. Comment *before* attribute.
first_attribute: int = 1
second_attribute = "abc"  #: str: The second module level attribute. *Inline* style.
third_attribute: list[int] = [1, 2, 3]
"""The third module level attribute. Docstring *after* attribute.

Multiple paragraphs are supported.
"""
not_attribute = 123  # Not attribute description because ':' is missing.


def add(x: int, y: int = 1) -> int:
    """Returns $x + y$.

    Args:
        x: The first parameter.
        y: The second parameter. Default={default}.

    Returns:
        Added value.

    Examples:
        Examples should be written in doctest format.

        >>> add(1, 2)
        3

    !!! note
        You can use the [Admonition extension of
        MkDocs](https://squidfunk.github.io/mkdocs-material/extensions/admonition/).

    Note:
        `Note` section is converted into the Admonition.
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
    """A normal class.

    Args:
        x: The first parameter.
        y: The second parameter.

    Raises:
        ValueError: If the length of `x` is equal to 0.
    """

    e: str
    """dde"""

    def __init__(self, x: list[int], y: tuple[str, int]):
        if len(x) == 0 or y[1] == 0:
            raise ValueError
        self.a: str = "abc"  #: The first attribute. Comment *inline* with attribute.
        #: The second attribute. Comment *before* attribute.
        self.b: dict[str, int] = {"a": 1}
        self.c = None
        """int, optional: The third attribute. Docstring *after* attribute.

        Multiple paragraphs are supported."""
        self.d = 100  # Not attribute description because ':' is missing.

    def message(self, n: int) -> list[str]:
        """Returns a message list.

        Args:
            n: Repetition.
        """
        return [self.a] * n

    @property
    def readonly_property(self):
        """str: Read-only property documentation."""
        return "readonly property"

    @property
    def readwrite_property(self) -> list[int]:
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
