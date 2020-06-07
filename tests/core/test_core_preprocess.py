from mkapi.core.preprocess import convert

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
