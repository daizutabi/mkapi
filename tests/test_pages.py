import inspect

from mkapi.pages import _split_markdown, _split_name_maxdepth


def test_split_name_maxdepth():
    assert _split_name_maxdepth("name") == ("name", 0)
    assert _split_name_maxdepth("name.*") == ("name", 1)
    assert _split_name_maxdepth("name.**") == ("name", 2)


def test_split_markdown():
    src = """
    # Title
    ## ::: a.o.Object|a|b
    text
    ### ::: a.s.Section
    ::: a.module|m
    end
    """
    src = inspect.cleandoc(src)
    x = list(_split_markdown(src))
    assert x[0] == ("# Title", -1, [])
    assert x[1] == ("a.o.Object", 2, ["a", "b"])
    assert x[2] == ("text", -1, [])
    assert x[3] == ("a.s.Section", 3, [])
    assert x[4] == ("a.module", 0, ["m"])
    assert x[5] == ("end", -1, [])
