from mkapi.core.preprocess import add_admonition, add_fence

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
