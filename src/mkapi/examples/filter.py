from collections.abc import Iterator


def func(x: int):
    """Function."""
    return x


def gen() -> Iterator[int]:
    """Generator."""
    yield 1


class C:
    """Class."""
