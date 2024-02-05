import doctest
import inspect
import re

import markdown

from mkapi.markdown import (
    _convert_examples,
    _iter,
    _iter_example,
    _iter_examples,
    _iter_fenced_code,
    add_link,
    finditer,
    replace_link,
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


def test_splitlines():
    x = "a\nb\n".splitlines()
    assert x == ["a", "b"]
    x = "a\n\nb\n".splitlines()
    assert x == ["a", "", "b"]


def test_split():
    text = "abcXdef"
    x = list(_iter(re.compile("X"), text))
    assert x[0] == "abc"
    assert x[2] == "def"
    text = "XabcXdefX"
    x = list(_iter(re.compile("X"), text))
    assert len(x) == 5
    assert x[1] == "abc"
    assert x[3] == "def"


def test_split_fenced_code():
    text = "abc\n  ~~~~x\n  ```\n  x\n  ```\n  ~~~~\ndef\n"
    x = list(_iter_fenced_code(text))
    assert len(x) == 3
    assert x[0] == "abc\n"
    assert x[2] == "def\n"
    for y in ["", "\n"]:
        text = f"abc\n  ~~~~x\n  ```\n  x\n  ```\n  ~~~~{y}"
        x = list(_iter_fenced_code(text))
        assert len(x) == 2
        assert x[0] == "abc\n"


def test_split_example():
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
    x = list(_iter_example(text))
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
    for t in ["abc\ndef\n", "abc\ndef", ">>> abc"]:
        assert list(_iter_example(t)) == [t]
    t = ">>> abc\n"
    x = list(_iter_example(t))
    assert len(x) == 1
    assert isinstance(x[0], doctest.Example)
    x = list(_iter_examples(text))
    assert len(x) == 8


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
    x = list(_iter_examples(src))
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

    ::: e
    f
    """
    src = inspect.cleandoc(src)
    x = list(finditer(pattern, src))
    assert len(x) == 9
    assert x[0] == "```\n# ::: a\n```\n"
    assert isinstance(x[1], re.Match)
    assert x[2] == "\n"
    assert isinstance(x[3], re.Match)
    assert x[4] == "\n"
    assert isinstance(x[5], str)
    assert x[5].startswith("```{.python")
    assert x[6] == "\n"
    assert isinstance(x[7], re.Match)
    assert x[8] == "\nf"


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

    def rel(m: re.Match):
        name = m.group("name")
        return f"xxx{name}xxx"

    m = sub(pattern, rel, src)
    print(m)
    assert m.startswith("```\n# ::: a\n```\nxxx::: bxxx\nxxx::: cxxx\n```{.python")
    assert m.endswith("output}\n::: d\n```\n\nxxx::: exxx\nf")


def c(text: str) -> str:
    text = inspect.cleandoc(text)
    e = ["admonition", "pymdownx.superfences", "attr_list", "md_in_html"]
    return markdown.markdown(text, extensions=e)


# def test_replace_directives():
#     src = """
#     abc

#     .. note::
#         a b c

#         d e f.

#     def
#     """
#     src = inspect.cleandoc(src)
#     text = replace_directives(src)
#     m = c(text)
#     assert '<p class="admonition-title">Note</p>' in m
#     assert "<p>a b c</p>" in m
#     assert "<p>d e f.</p>\n</div>" in m


# def test_replace_directives_deprecated():
#     src = """
#     abc

#     .. deprecated:: 1.0
#         xyz

#     def
#     """
#     src = inspect.cleandoc(src)
#     text = replace_directives(src)
#     m = c(text)
#     assert '<p class="admonition-title">Deprecated since version 1.0</p>' in m


# def test_replace_directives_codeblock():
#     src = """
#     abc

#     .. note::
#         a b c

#           .. code-block:: python

#             a = 1

#             b = 1

#         d e f
#     """
#     src = inspect.cleandoc(src)
#     text = replace_directives(src)
#     m = c(text)
#     assert '<div class="admonition note">' in m
#     assert "<p>a b c</p>\n<pre><code>a = 1\n\nb = 1\n</code></pre>" in m


def test_replace_link():
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
    text = replace_link(src)
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
