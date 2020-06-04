"""md
# Type Annotation Examples

{{ # cache:clear }}

Import libraries and create a Markdown conveter.
"""

from IPython.display import HTML
from markdown import Markdown

import mkapi

converter = Markdown()

# ## Helper Function

# Define a helper function that performs everything at one step.


def render(obj):
    node = mkapi.get_node(obj)
    markdown = node.get_markdown()
    html = converter.convert(markdown)
    node.set_html(html)
    html = node.render()
    return HTML(html)


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


render(builtin)

# ## Builtin Types with Default


def builtin_default(i: int = 1, f: float = 1.0, s: str = "abc", t: tuple = (1, 2)):
    """Function with buitin type annotation and default.

    Args:
        i: Integer.
        f: Float.
        s: String.
        t: Tuple.
    """


render(builtin_default)

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


render(basic)

# ## Iterator, Iterable

from typing import Iterator, Iterable  # isort:skip


def function(x: Iterable[str]) -> Iterator[str]:
    """Function that returns an iterator.

    Args:
        x: Iterable of string
    """
    return iter(x)


render(function)


# -
def generator(x: Iterable[str]) -> Iterator[str]:
    """Generator that yields string."""
    yield from x


render(generator)


# ## Union, Optional

from typing import Optional, Union  # isort:skip


def optional(x: Optional[List[int]]):
    """Function with optional list.

    Args:
        x: List of integer.
    """


render(optional)

# -


def optional_default(x: Optional[List[int]] = None):
    """Function with optional list and default.

    Args:
        x: List of integer.
    """


render(optional_default)

# -


def union(x: Union[int, float], y: Union[int, str, dict]):
    """Function with union of builtin.

    Args:
        x: Integer or float.
        y: Integer, string, or dictionary.
    """


render(union)
# -


def union_collection(x: Union[List[int], Tuple[str, str]]):
    """Function with union of collection.

    Args:
        x: List of integer or tuple of (string, string).
    """


render(union_collection)
