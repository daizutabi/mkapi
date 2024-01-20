from mkapi.importlib import get_object


def test_a():
    obj = get_object("polars.dataframe.frame.DataFrame.dtypes")
    assert obj
