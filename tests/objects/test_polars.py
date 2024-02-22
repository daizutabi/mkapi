from mkapi.nodes import resolve, resolve_from_module


def test_resolve():
    assert resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert resolve("polars.col") == "polars.functions.col"
    assert resolve("polars.row") == "polars.row"
    assert resolve("polars.api") == "polars.api"


def test_resolve_from_module():
    x = resolve_from_module("DataType", "polars.dataframe.frame")
    assert x == "polars.datatypes.classes.DataType"
    assert resolve_from_module("api", "polars") == "polars.api"
    assert resolve_from_module("exceptions", "polars") == "polars.exceptions"
