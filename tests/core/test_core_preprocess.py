from mkapi.core.preprocess import admonition, convert

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


def test_convert():
    assert convert(source) == output


def test_admonition():
    markdown = admonition("Warnings", "abc\n\ndef")
    assert markdown == '!!! warning "Warnings"\n    abc\n\n    def'
    markdown = admonition("Note", "abc\n\ndef")
    assert markdown == '!!! note "Note"\n    abc\n\n    def'
    markdown = admonition("Tips", "abc\n\ndef")
    assert markdown == '!!! tips "Tips"\n    abc\n\n    def'
