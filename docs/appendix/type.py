"""md
# Type Annotation Examples

{{ # cache:clear }}


<style type="text/css">  <!-- .mkapi-node {   border: 2px dashed #88AA88; } -->
</style>

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
def iterator(x: Iterable[str]) -> Iterator[str]:
    """Iterator that yields string."""
    yield from x


mkapi.display(iterator)


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

# ## Callable

from typing import Callable  # isort:skip


def callable(
    x: Callable,
    y: Callable[[int], str],
    z: Callable[[List[str], Tuple[float]], Dict[str, str]],
) -> Callable[..., int]:
    """Callable.

    Args:
        x: Without arguments.
        y: Builtins.
        z: Using `typing` module.



    """


mkapi.display(callable)


# ## Generator

from typing import Generator, AsyncGenerator  # isort:skip


def generator(
    x: Generator[int, float, str],
    y: Generator[int, float, None],
    z: Generator[int, None, List[str]],
) -> Generator[int, None, None]:
    """Generator.

    Args:
        x: Yield type, send type, and return type.
        y: Yield type and send type.
        z: Yield type and return type.
    """


mkapi.display(generator)
# -


def async_generator(x: AsyncGenerator[int, float], y: AsyncGenerator[int, None]):
    """AsyncGenerator.

    Args:
        x: Yield type and send type.
        y: Yield type.
    """


mkapi.display(async_generator)
