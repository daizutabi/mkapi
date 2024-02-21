from mkapi.objects import get_fullname, get_members_all, resolve


def test_resolve():
    assert resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert resolve("polars.col") == "polars.functions.col"
    assert resolve("polars.row") == "polars.row"
    assert resolve("polars.api") == "polars.api"


def test_get_fullname():
    x = get_fullname("DataType", "polars.dataframe.frame")
    assert x == "polars.datatypes.classes.DataType"
    assert get_fullname("exceptions", "polars") == "polars.exceptions"
    assert get_fullname("api", "polars") == "polars.api"


def test_get_all():
    x = get_members_all("polars")
    assert x["api"].name == "polars.api"  # type: ignore
    assert x["ArrowError"].module == "polars.exceptions"  # type: ignore
