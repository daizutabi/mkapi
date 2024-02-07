import doctest
import inspect
import re

import markdown

from mkapi.markdown import (
    _convert_code_block,
    _convert_examples,
    _iter,
    _iter_example_lists,
    _iter_examples,
    _iter_fenced_codes,
    _iter_literal_block,
    _replace,
    _split_block,
    add_link,
    convert,
    finditer,
    sub,
)


def test_id():
    name = "m.__a__".replace("_", "\\_")
    h = markdown.markdown(f"[{name}](b){{#{name}}}", extensions=["attr_list"])
    assert h == '<p><a href="b" id="m.__a__">m.__a__</a></p>'
    h = markdown.markdown(f"# {name} {{#{name}}}", extensions=["attr_list"])
    assert h == '<h1 id="m.__a__">m.__a__</h1>'
    h = markdown.markdown(f"{name}\n{{#{name}}}", extensions=["attr_list"])
    assert h == '<p id="m.__a__">m.__a__</p>'


def test_md_in_html():
    m = '<div id="__a__" markdown="1">\n# t\n</div>'
    h = markdown.markdown(m, extensions=["md_in_html"])
    assert h == '<div id="__a__">\n<h1>t</h1>\n</div>'


def test_link():
    name = "__a__"
    h = markdown.markdown(f"[abc](ref#{name})")
    assert h == '<p><a href="ref#__a__">abc</a></p>'


def test_span():
    x = markdown.markdown('<span class="c">[a](b)</span>')
    assert x == '<p><span class="c"><a href="b">a</a></span></p>'


def test_list():
    s = "a\n\n    b"
    x = markdown.markdown(s)
    assert "<pre><code>b" in x
    s = "a\n\n    * b\n    * c\n"
    x = markdown.markdown(s)
    assert "<pre><code>* b" in x


def c(text: str) -> str:
    return markdown.markdown(text, extensions=["admonition"])


def test_code():
    x = c("a b\n    c")
    assert x == "<p>a b\n    c</p>"
    x = c("a b\n\n    c")
    assert x == "<p>a b</p>\n<pre><code>c\n</code></pre>"
    x = c("a b\n\n    c\n\n    d")
    assert "<code>c\n\nd\n</code>" in x
    x = c("a b\n\n    c\n\n    d\ne")
    assert "<code>c\n\nd\n</code>" in x


def test_fenced_code():
    x = c("```\na\n```")
    assert x == "<p><code>a</code></p>"
    x = c("    ```\n    a\n    ```")
    assert "```" in x
    x = c("  ```\na\n  ```")
    assert x == "<p><code>a</code></p>"
    x = c("!!! note\n    ```\n    a\n    ```")
    assert '<p class="admonition-title">Note</p>\n<p><code>a</code></p>' in x
    x = c("!!! note\n  ```\n  a\n  ```")
    assert '<p class="admonition-title">Note</p>\n</div>' in x


def test_splitlines():
    x = "a\nb\n".splitlines()
    assert x == ["a", "b"]
    x = "a\n\nb\n".splitlines()
    assert x == ["a", "", "b"]
    x = "".splitlines()
    assert x == []


def test_iter():
    pattern = re.compile("X")
    text = "abcXdef"
    x = list(_iter(pattern, text))
    assert x[0] == "abc"
    assert x[2] == "def"
    text = "XabcXdefX"
    x = list(_iter(pattern, text))
    assert len(x) == 5
    assert x[1] == "abc"
    assert x[3] == "def"
    text = "abc\n"
    x = list(_iter(pattern, text))
    assert x == ["abc\n"]
    text = "X"
    x = list(_iter(pattern, text))
    assert len(x) == 1


def test_iter_fenced_codes():
    text = "abc\n~~~~x\n```\nx\n```\n~~~~\ndef\n"
    x = list(_iter_fenced_codes(text))
    assert len(x) == 3
    assert x[0] == "abc\n"
    assert x[2] == "def\n"
    for y in ["", "\n"]:
        text = f"abc\n~~~~x\n```\nx\n```\n~~~~{y}"
        x = list(_iter_fenced_codes(text))
        assert len(x) == 2
        assert x[0] == "abc\n"
    text = "abc\n"
    x = list(_iter_fenced_codes(text))
    assert x == ["abc\n"]


def test_iter_examples():
    text = """
    X
      >>> a = 1
      >>> # comment

      Y
        >>> a  # doctest: aaa
        1
        >>>
        >>> a = 1

    >>> a
    1

    Z
    """
    text = inspect.cleandoc(text)
    x = list(_iter_examples(text))
    assert len(x) == 10
    assert x[0] == "X\n"
    assert isinstance(x[1], doctest.Example)
    assert x[1].source == "a = 1\n"
    assert x[1].indent == 2
    assert isinstance(x[2], doctest.Example)
    assert x[2].source == "# comment\n"
    assert x[2].indent == 2
    assert isinstance(x[4], doctest.Example)
    assert x[3] == "\n  Y\n"
    assert x[4].source == "a\n"
    assert x[4].indent == 4
    assert isinstance(x[5], doctest.Example)
    assert x[5].source == "\n"
    assert x[5].indent == 4
    assert isinstance(x[6], doctest.Example)
    assert x[6].source == "a = 1\n"
    assert x[7] == "\n"
    assert isinstance(x[8], doctest.Example)
    assert x[8].source == "a\n"
    assert x[8].want == "1\n"
    assert x[9] == "\nZ"
    x = list(_iter_example_lists(text))
    assert len(x) == 8
    t = ">>> abc\n"
    x = list(_iter_examples(t))
    assert len(x) == 1
    assert isinstance(x[0], doctest.Example)


def test_iter_examples_empty():
    for t in ["a", "a\n", "abc\ndef\n", "abc\ndef", ">>> abc"]:
        assert list(_iter_examples(t)) == [t]


def test_convert_examples():
    src = """
    >>>  1 # input
    1
      >>> a = 2
      >>> a
      2
    >>> a = 3
    """
    src = inspect.cleandoc(src)
    x = list(_iter_example_lists(src))
    assert len(x) == 3
    assert isinstance(x[0], list)
    m = _convert_examples(x[0])
    assert "input}\n 1 #" in m
    assert "output}\n1\n```\n" in m
    assert isinstance(x[1], list)
    m = _convert_examples(x[1])
    assert "input}\n  a = 2\n  a\n  ```\n" in m
    assert "output}\n  2\n  ```\n" in m
    assert isinstance(x[2], list)
    m = _convert_examples(x[2])
    assert m.endswith("input}\na = 3\n```\n")


def test_split_block():
    src = "\n a\n b\n\n c\nd\n"
    x, y = _split_block(src, 0)
    assert x == "\n a\n b\n\n c\n"
    assert f"{x}{y}" == src
    src = "\n a\n b\n\n c\n"
    x, y = _split_block(src, 0)
    assert (x, y) == (src, "")
    src = "a\nb\n"
    x, y = _split_block(src, 0)
    assert (x, y) == ("", src)


def test_iter_literal_block():
    src = " x\n a\n\n\n     b\n\n     c\n\nd\n"
    x = "".join(list(_iter_literal_block(src)))
    assert x == " x\n a\n\n\n ```\n b\n\n c\n ```\n\nd\n"


def test_convert_code_block():
    src = """
    ```
    ab

        d
    x
    ```
      x

          x

          y

      >>> 1
      1
    """
    src = inspect.cleandoc(src)
    m = _convert_code_block(src)
    assert "```\nab\n\n    d\nx\n```\n" in m
    assert "  x\n\n  ```\n  x\n\n  y\n  ```\n" in m
    assert "\n  ```{.python" in m


def test_convert_literal_block_with_directive():
    src = """
    a
      .. code-block:: python

          a
      d
      .. note::

          a
      d

          b
    """
    src = inspect.cleandoc(src)
    m = _convert_code_block(src)
    assert m.startswith("a\n  ```python\n  a\n  ```\n  d\n")
    assert "  .. note::\n\n      a" in m
    assert m.endswith("  d\n\n  ```\n  b\n  ```\n")


def test_convert():
    src = """
    ```
    .. note::
    ```
    .. note::
        abc

            d
        .. note::

            def
    .. note::
        x
    """
    src = inspect.cleandoc(src)
    m = convert(src)
    h = c(m)
    assert "<p><code>.. note::</code></p>" in h
    assert "Note</p>\n<p>abc</p>\n<p><code>d</code></p>" in h
    assert "<p>def</p>\n</div>\n</div>" in h


def test_convert_example_new_line():
    src1 = """
    a
      >>> 1
      1

      >>> 2
      2
    """
    src2 = """
    a
      >>> 1
      1
      >>> 2
      2
    """
    src1 = inspect.cleandoc(src1)
    src2 = inspect.cleandoc(src2)
    assert convert(src1) == convert(src2)


def test_finditer():
    pattern = re.compile(r"^(?P<pre>#* *)(?P<name>:::.*)$", re.M)
    src = """
    ```
    # ::: a
    ```
    ## ::: b
    ::: c
    >>> "::: d"
    ::: d

    a

        ::: e
    f
    """
    src = inspect.cleandoc(src)
    src = convert(src)
    x = list(finditer(pattern, src))
    assert isinstance(x[1], re.Match)
    assert isinstance(x[3], re.Match)


def test_sub():
    pattern = re.compile(r"^(?P<pre>#* *)(?P<name>:::.*)$", re.M)
    src = """
    ```
    # ::: a
    ```
    ## ::: b
    ::: c
    >>> "::: d"
    ::: d

    ::: e
    f
    """
    src = inspect.cleandoc(src)
    src = convert(src)

    def rel(m: re.Match):
        name = m.group("name")
        return f"xxx{name}xxx"

    m = sub(pattern, rel, src)
    print(m)
    assert m.startswith("```\n# ::: a\n```\nxxx::: bxxx\nxxx::: cxxx\n```{.python")
    assert m.endswith("output}\n::: d\n```\n\nxxx::: exxx\nf")


def test_replace():
    src = """
    `abc <def>`_
    :func:`ghi <jkl>`
    :func:`mno`
    `xxx`_ `yy
    y`_
    .. _xxx:
    XXX
    zzz
    .. _yyy: YYY
    """
    src = inspect.cleandoc(src)
    text = _replace(src)
    lines = text.splitlines()
    assert lines[0] == "[abc](def)"
    assert lines[1] == "[ghi][__mkapi__.jkl]"
    assert lines[2] == "[__mkapi__.mno][]"
    assert lines[3] == "[xxx][] [yy"
    assert lines[4] == "y][]"
    assert "[xxx]:\nXXX\nzzz\n[yyy]: YYY" in text


def test_add_link():
    src = """
    abc, def
    ghi: jkl
    """
    src = inspect.cleandoc(src)
    text = add_link(src)
    assert text
    assert "[__mkapi__.abc][], [__mkapi__.def][]\n" in text
    assert "[__mkapi__.ghi][]: jkl" in text


def test_add_link_items():
    src = """
    abc: def
    ghi: jkl
        mno
    pqr: stu
    """
    src = inspect.cleandoc(src)
    text = add_link(src)
    lines = text.splitlines()
    assert lines[0] == "* [__mkapi__.abc][]: def"
    assert lines[1] == "* [__mkapi__.ghi][]: jkl mno"
    assert lines[2] == "* [__mkapi__.pqr][]: stu"
