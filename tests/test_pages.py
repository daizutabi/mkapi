from mkapi.pages import _split_name_maxdepth


def test_split_name_maxdepth():
    assert _split_name_maxdepth("name") == ("name", 0)
    assert _split_name_maxdepth("name.*") == ("name", 1)
    assert _split_name_maxdepth("name.**") == ("name", 2)


# LazyFrame.tail
