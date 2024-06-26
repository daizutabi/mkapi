import pytest

from mkapi.globals import (
    _iter_objects_from_all,
    get_all,
    get_fullname,
    get_globals,
    resolve,
)
from mkapi.items import Parameters, SeeAlso
from mkapi.objects import (
    Attribute,
    Class,
    Function,
    create_module,
    iter_objects,
)
from mkapi.utils import get_by_name, get_by_type, get_module_node, iter_by_name


def test_iter_objects_polars():
    name = "polars.dataframe.frame"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    x = list(iter_objects(module, 0))
    assert len(x) == 1
    x = list(iter_objects(module, 1))
    assert get_by_name(x, "DataFrame")
    assert not get_by_name(x, "product")
    x = list(iter_objects(module, 2))
    assert get_by_name(x, "DataFrame")
    assert get_by_name(x, "product")


@pytest.fixture(scope="module")
def DataFrame() -> Class:  # noqa: N802
    node = get_module_node("polars.dataframe.frame")
    assert node
    module = create_module("polars.dataframe.frame", node)
    assert module
    cls = get_by_name(module.classes, "DataFrame")
    assert isinstance(cls, Class)
    return cls


def test_set_markdown_polars(DataFrame: Class):  # noqa: N803
    obj = DataFrame
    m = obj.doc.type.markdown
    assert "[polars][__mkapi__.polars]..[dataframe]" in m
    assert "[__mkapi__.polars.dataframe]..[frame]" in m
    assert "[__mkapi__.polars.dataframe.frame]" in m
    func = get_by_name(obj.functions, "write_excel")
    assert isinstance(func, Function)
    p = func.parameters[1]
    assert "[Workbook][__mkapi__.xlsxwriter.Workbook]" in p.type.markdown


def test_set_markdown_object(DataFrame: Class):  # noqa: N803
    attr = get_by_name(DataFrame.attributes, "width")
    assert isinstance(attr, Attribute)
    assert attr.type.markdown == "int"


def test_iter_merged_parameters(DataFrame: Class):  # noqa: N803
    func = get_by_name(DataFrame.functions, "pipe")
    assert isinstance(func, Function)
    params = get_by_type(func.doc.sections, Parameters)
    assert params
    x = params.items
    assert x[0].name == "function"
    assert "typing.Callable][[Concatenate][__mkapi__" in x[0].type.markdown
    assert x[1].name == "*args"
    assert "[P][__mkapi_" in x[1].type.markdown
    assert x[2].name == "**kwargs"
    assert "frame.P].[kwargs][__" in x[2].type.markdown


def test_see_also(DataFrame: Class):  # noqa: N803
    func = get_by_name(DataFrame.functions, "head")
    assert isinstance(func, Function)
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    assert "[__mkapi__.polars.dataframe.frame.DataFrame.tail]" in see.text.markdown
    func = get_by_name(DataFrame.functions, "_read_csv")
    assert isinstance(func, Function)
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    assert "[__mkapi__.polars.io.csv.functions.read_csv]" in see.text.markdown


def test_see_also_text():
    name = "polars.lazyframe.frame"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    cls = get_by_name(module.classes, "LazyFrame")
    assert isinstance(cls, Class)
    attr = get_by_name(cls.attributes, "dtypes")
    assert attr
    see = get_by_type(attr.doc.sections, SeeAlso)
    assert see
    m = see.text.markdown
    assert "[schema][__mkapi__.polars.lazyframe.frame.LazyFrame.schema]" in m
    assert "Returns a" in m
    func = get_by_name(cls.functions, "deserialize")
    assert func
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    m = see.text.markdown
    assert "[__mkapi__.polars.lazyframe.frame.LazyFrame.serialize]" in m
    name = "polars.io.csv.functions"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    func = get_by_name(module.functions, "read_csv")
    assert func
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    m = see.text.markdown
    assert "[__mkapi__.polars.io.csv.functions.scan_csv]" in m


def test_property():
    name = "polars.dataframe.frame"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    cls = get_by_name(module.classes, "DataFrame")
    assert isinstance(cls, Class)
    assert not get_by_name(cls.functions, "plot")
    assert get_by_name(cls.attributes, "plot")


def test_overload():
    name = "polars.functions.repeat"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert len(list(iter_by_name(module.functions, "repeat"))) == 1
    func = get_by_name(module.functions, "repeat")
    assert isinstance(func, Function)
    assert func.doc.sections


def test_resolve():
    assert resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert resolve("polars.col") == "polars.functions.col"
    assert resolve("polars.row") is None


def test_get_globals():
    x = get_globals("polars.dataframe.frame")
    n = get_by_name(x.names, "Workbook")
    assert n


def test_get_fullname():
    x = get_fullname("polars.dataframe.frame", "DataType")
    assert x == "polars.datatypes.classes.DataType"
    x = get_fullname("polars.dataframe.frame", "Workbook")
    assert x == "xlsxwriter.Workbook"
    assert get_fullname("polars", "exceptions") == "polars.exceptions"
    assert get_fullname("polars", "api") == "polars.api"


def test_iter_objects_from_all():
    x = list(_iter_objects_from_all("polars"))
    assert "polars.DataFrame" in x
    assert "polars.first" in x


def test_get_all():
    x = get_all("polars")
    assert x["api"] == "polars.api"
    assert x["ArrowError"] == "polars.exceptions.ArrowError"


# LazyFrame.tail
