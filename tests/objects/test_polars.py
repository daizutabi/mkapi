from mkapi.nodes import resolve


def test_resolve():
    assert resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert resolve("polars.col") == "polars.functions.col"
    assert resolve("polars.row") == "polars.row"
    assert resolve("polars.api") == "polars.api"
    x = resolve("DataType", "polars.dataframe.frame")
    assert x == "polars.datatypes.classes.DataType"
    assert resolve("exceptions", "polars") == "polars.exceptions"
    assert resolve("api", "polars") == "polars.api"
