import textwrap

from mkapi.parser import clean_item_text


def test_clean_item_text():
    text = textwrap.dedent("""\
    a
    b
    c
    d""")
    assert clean_item_text(text) == "a\nb\nc\nd"


def test_clean_item_text_list():
    text = textwrap.dedent("""\
    a
    - b
    - c
    d""")
    x = clean_item_text(text)
    assert x == "a\n\n- b\n- c\n\nd"


def test_clean_item_text_list_and_indent():
    text = textwrap.dedent("""\
    a
    - b
      B
    - c
      C
    d""")
    x = clean_item_text(text)
    assert x == "a\n\n- b\n  B\n- c\n  C\n\nd"


def test_clean_item_text_list_with_blank_line():
    text = textwrap.dedent("""\
    a

    - b
    - c

    d""")
    assert clean_item_text(text) == text


def test_clean_item_text_list_with_blank_line_and_indent():
    text = textwrap.dedent("""\
    a

    - b
      B
    - c
      C

    d""")
    assert clean_item_text(text) == text
