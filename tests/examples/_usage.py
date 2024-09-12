from mkapi.doc import Item as I
from mkapi.node import Definition as D  # noqa: F401
from mkapi.object import Object


def func(a: Object, b) -> I:
    """
    Docstring `D`.

    Args:
        a: A.
        b (D): B `I` `Object`.

    Returns:
        C.
    """
    return I("x", "int", "Docstring.")


class A:
    """
    Docstring `I`.
    """

    x: D
    """Attribute `D`."""
