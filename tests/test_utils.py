from mkapi.utils import add_admonition, add_fence, find_submodule_names, get_by_name


def test_find_submodule_names():
    names = find_submodule_names("mkdocs")
    assert "mkdocs.commands" in names
    assert "mkdocs.plugins" in names


source = """ABC

>>> 1 + 2
3

DEF

>>> 3 + 4
7

GHI
"""

output = """ABC

~~~python
>>> 1 + 2
3
~~~

DEF

~~~python
>>> 3 + 4
7
~~~

GHI"""


def test_add_fence():
    assert add_fence(source) == output


def test_add_admonition():
    markdown = add_admonition("Warnings", "abc\n\ndef")
    assert markdown == '!!! warning "Warnings"\n    abc\n\n    def'
    markdown = add_admonition("Note", "abc\n\ndef")
    assert markdown == '!!! note "Note"\n    abc\n\n    def'
    markdown = add_admonition("Tips", "abc\n\ndef")
    assert markdown == '!!! tips "Tips"\n    abc\n\n    def'


class A:
    def __init__(self, name):
        self.name = name


def test_get_by_name():
    items = [A("a"), A("b"), A("c")]
    assert get_by_name(items, "b").name == "b"  # type: ignore
    assert get_by_name(items, "x") is None
