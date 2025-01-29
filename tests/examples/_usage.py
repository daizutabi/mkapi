from astdoc.doc import Item as I
from astdoc.node import Definition as D  # noqa: F401
from astdoc.object import Object


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
