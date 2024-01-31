import inspect

import markdown

from mkapi.markdown import (
    add_link,
    replace_directives,
    replace_examples,
    replace_link,
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


def test_replace_link():
    src = """
    `abc <def>`_
    :func:`ghi <jkl>`
    :func:`mno`
    """
    src = inspect.cleandoc(src)
    lines = replace_link(src).splitlines()
    assert lines[0] == "[abc](def)"
    assert lines[1] == "[ghi][__mkapi__.jkl]"
    assert lines[2] == "[__mkapi__.mno][]"


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


def c(text: str) -> str:
    text = inspect.cleandoc(text)
    e = ["admonition", "pymdownx.superfences", "attr_list", "md_in_html"]
    return markdown.markdown(text, extensions=e)


def test_replace_examples():
    src = """
    !!! Note

        abc

        >>> a = 1
        >>> print(a)
        1

        def

         >>> def f():
         ...    pass

        ghi

    jkl
    """
    src = inspect.cleandoc(src)
    text = replace_examples(src)
    m = c(text)
    assert '<div class="admonition note">' in m
    assert '<p><div class="mkapi-example" mkarkdown="1">' in m
    assert '<div class="mkapi-example-input highlight">' in m
    assert '<div class="mkapi-example-output highlight">' in m


def test_replace_examples_prompt_only():
    src = """
    abc

    >>> a = 1
    >>>
    >>> b = 1
    """
    src = inspect.cleandoc(src)
    text = replace_examples(src)
    assert "\n```{.python .mkapi-example-input}\na = 1\n\nb = 1" in text


def test_replace_directives():
    src = """
    abc

    .. note::
        a b c

        d e f.

    def
    """
    src = inspect.cleandoc(src)
    text = replace_directives(src)
    m = c(text)
    assert '<p class="admonition-title">Note</p>' in m
    assert "<p>a b c</p>" in m
    assert "<p>d e f.</p>\n</div>" in m


def test_replace_directives_deprecated():
    src = """
    abc

    .. deprecated:: 1.0
        xyz

    def
    """
    src = inspect.cleandoc(src)
    text = replace_directives(src)
    m = c(text)
    assert '<p class="admonition-title">Deprecated since version 1.0</p>' in m


def test_replace_directives_codeblock():
    src = """
    abc

    .. note::
        a b c

          .. code-block:: python

          a = 1

          b = 1

        d e f

    .. note::
        a b c

           .. code-block:: python

             a = 1

             b = 1

        d e f

    """
    src = inspect.cleandoc(src)
    text = replace_directives(src)
    print(text)
    m = c(text)
    print(m)
    assert 0
