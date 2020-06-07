"""md
# Type Annotation Examples

{{ # cache:clear }}
"""

import mkapi

# ## Builtin Types


def builtin(i: int, f: float, s: str, l: list, d: dict, t: tuple, e: set) -> bool:
    """Function with buitin type annotation.

    Args:
        i: Integer.
        f: Float.
        s: String.
        l: List.
        d: Dictionary.
        t: Tuple.
        e: Set.
    """
    return True


mkapi.display(builtin)

# ## Builtin Types with Default


def builtin_default(i: int = 1, f: float = 1.0, s: str = "abc", t: tuple = (1, 2)):
    """Function with buitin type annotation and default.

    Args:
        i: Integer. Default={default}.
        f: Float. Default={default}.
        s: String. Default={default}.
        t: Tuple. Default={default}.
    """


mkapi.display(builtin_default)

# ## Basic Collection Types

from typing import Dict, List, Set, Tuple  # isort:skip


def basic(l: List[int], t: Tuple[str, int, float], d: Dict[str, int], s: Set[int]):
    """Function with basic collection type annotation.

    Args:
        l: List of integer.
        t: Tuple of (string, string).
        d: Dictionary from string to integer.
        s: Set of integer.
    """


mkapi.display(basic)

# ## Iterator and Iterable

from typing import Iterator, Iterable  # isort:skip


def function(x: Iterable[str]) -> Iterator[str]:
    """Function that returns an iterator.

    Args:
        x: Iterable of string
    """
    return iter(x)


mkapi.display(function)


# -
def generator(x: Iterable[str]) -> Iterator[str]:
    """Generator that yields string."""
    yield from x


mkapi.display(generator)


# ## Union and Optional

from typing import Optional, Union  # isort:skip


def optional(x: Optional[List[int]]):
    """Function with optional list.

    Args:
        x: List of integer or None.
    """


mkapi.display(optional)

# -


def optional_default(x: Optional[List[int]] = None):
    """Function with optional list and default.

    Args:
        x: List of integer or None
    """


mkapi.display(optional_default)

# -


def union(x: Union[int, float], y: Union[int, str, dict]):
    """Function with union of builtin.

    Args:
        x: Integer or float.
        y: Integer, string, or dictionary.
    """


mkapi.display(union)
# -


def union_collection(x: Union[List[int], Tuple[str, str]]):
    """Function with union of collection.

    Args:
        x: List of integer or tuple of (string, string).
    """


mkapi.display(union_collection)
