"""md
# Type Annotation Examples

{{ # cache:clear }}

Import libraries and create a Markdown conveter.
"""
from typing import Any, Dict, List, Set, Tuple

from IPython.display import HTML
from markdown import Markdown

import mkapi

converter = Markdown()

# ## Helper Function

# Define a helper function that performs everything at one step.


def render(obj: Any):
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
    """Function with buitin type annotation.

    Args:
        i: Integer.
        f: Float.
        s: String.
        t: String.
    """
    return True


render(builtin_default)

# ## Basic Collection Types


def basic(l: List[int], t: Tuple[str, int, float], d: Dict[str, int], s: Set[int]):
    """Function with basic generic type annotation.

    Args:
        l: List of int.
        t: Tuple of (str, str).
        d: Dictionary from str to int.
        s: Set of int.
    """
    return set([1, 2, 3])


render(basic)
