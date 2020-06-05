from dataclasses import dataclass

import pytest

import mkapi
from mkapi.core.inherit import get_params, inherit, is_complete


@dataclass
class A:
    """Base class.

    Parameters:
        name: Object name.
        type: Object type

    Attributes:
        name: Object name.
        type: Object type
    """

    name: str
    type: str = ""


@dataclass
class B(A):
    """Item class.

    Parameters:
        markdown: Object markdown

    Attributes:
        markdown: Object markdown
    """

    markdown: str = ""


mkapi.get_node(A)

@pytest.fixture()
def a():
    return mkapi.get_node(A)


@pytest.fixture()
def b():
    return mkapi.get_node(B)


def test_is_complete(a, b):
    assert is_complete(a)
    assert not is_complete(b)


@pytest.mark.parametrize("name", ["Parameters", "Attributes"])
def test_get_params(a, b, name):
    a_doc_params, a_sig_params = get_params(a, name)
    assert len(a_doc_params) == 2
    assert len(a_sig_params) == 2

    b_doc_params, b_sig_params = get_params(b, name)
    assert len(b_doc_params) == 1
    assert len(b_sig_params) == 3


def test_inherit(b):
    inherit(b)
    assert is_complete(b)


@pytest.mark.parametrize("name", ["Parameters", "Attributes"])
def test_get_params_after(b, name):
    b_doc_params, b_sig_params = get_params(b, name)
    assert len(b_doc_params) == 3
    assert len(b_sig_params) == 3
