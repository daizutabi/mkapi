"""Module level docstring."""
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Tuple


def add(x: int, y: int = 1) -> int:
    """Returns $x + y$.

    Parameters
    ----------
    x
        The first parameter.
    y
        The second parameter. Default={default}.

    Returns
    -------
    int
        Added value.

        !!! note
            The return type must be duplicated in the docstring to comply with the NumPy
            docstring style.

    Examples
    --------
    Examples should be written in doctest format.

    >>> add(1, 2)
    3

    Note
    ----
        MkApi doesn't check an underline that follows a section heading.
        Just skip one line.
    """
    return x + y


def gen(n) -> Iterator[str]:
    """Yields a numbered string.

    Parameters
    ----------
    n : int
        The length of iteration.

    Yields
    ------
    str
        A numbered string.
    """
    for x in range(n):
        yield f"a{x}"


class ExampleClass:
    """A normal class.

    Parameters
    ----------
    x
        The first parameter.
    y
        The second parameter.

    Raises
    ------
    ValueError
        If the length of `x` is equal to 0.
    """

    def __init__(self, x: List[int], y: Tuple[str, int]):
        if len(x) == 0:
            raise ValueError()
        self.a: str = "abc"  #: The first attribute. Comment *inline* with attribute.
        #: The second attribute. Comment *before* attribute.
        self.b: Dict[str, int] = {"a": 1}
        self.c = None
        """int, optional: The third attribute. Docstring *after* attribute.

        Multiple paragraphs are supported."""
        self.d = 100  # Not attribute description because ':' is missing.

    def message(self, n: int) -> List[str]:
        """Returns a message list.

        Parameters
        ----------
        n
            Repetition.
        """
        return [self.a] * n

    @property
    def readonly_property(self):
        """str: Read-only property documentation."""
        return "readonly property"

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

    Parameters
    ----------
    x
        The first parameter.

    Attributes
    ----------
    x
        The first attribute.
    y
        The second attribute.
    """

    x: int = 0
    y: int = field(default=1, init=False)
