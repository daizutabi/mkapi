from mkapi.core.node import get_node


class A:
    """Class docstring."""

    def __init__(self):
        pass

    def func(self):
        """Function docstring."""


def test_class_docstring():
    node = get_node(A)
    assert node.docstring.sections[0].markdown == "Class docstring."
    assert len(node.members) == 1


class B:
    def __init__(self):
        """Init docstring."""

    def func(self):
        """Function docstring."""


def test_init_docstring():
    node = get_node(B)
    assert node.docstring.sections[0].markdown == "Init docstring."
    assert len(node.members) == 1


class C:
    """Class docstring."""

    def __init__(self):
        """Init docstring."""

    def func(self):
        """Function docstring."""


def test_class_and_init_docstring():
    node = get_node(C)
    assert node.docstring.sections[0].markdown == "Class docstring."
    assert len(node.members) == 1


class D:
    def __init__(self):
        pass

    def func(self):
        """Function docstring."""


def test_without_docstring():
    node = get_node(D)
    assert not node.docstring
    assert len(node.members) == 1


class E:
    """Class docstring."""

    def func(self):
        """Function docstring."""


def test_without_init():
    node = get_node(E)
    assert node.docstring.sections[0].markdown == "Class docstring."
    assert len(node.members) == 1
