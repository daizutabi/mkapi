import pytest

from mkapi.inspect import (
    get_all,
    get_fullname,
    resolve,
)
from mkapi.items import Parameters, SeeAlso
from mkapi.link import set_markdown
from mkapi.objects import (
    Attribute,
    Class,
    Function,
    _create_module,
    create_module,
    iter_objects,
)
from mkapi.utils import get_by_name, get_by_type, get_module_node, iter_by_name


def test_iter_objects_polars():
    name = "polars.dataframe.frame"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
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
    module = _create_module("polars.dataframe.frame", node)
    assert module
    cls = get_by_name(module.classes, "DataFrame")
    assert isinstance(cls, Class)
    return cls


def test_set_markdown_polars(DataFrame: Class):  # noqa: N803
    obj = DataFrame
    set_markdown(obj)
    m = obj.name.markdown
    assert m == "[DataFrame][__mkapi__.polars.dataframe.frame.DataFrame]"
    m = obj.fullname.markdown
    assert "[polars][__mkapi__.polars].[dataframe]" in m
    assert "[__mkapi__.polars.dataframe].[frame]" in m
    assert "[__mkapi__.polars.dataframe.frame]" in m
    func = get_by_name(obj.functions, "write_excel")
    assert isinstance(func, Function)
    set_markdown(func)
    p = func.parameters[1]
    assert "[Workbook][__mkapi__.xlsxwriter.Workbook]" in p.type.markdown


def test_set_markdown_object(DataFrame: Class):  # noqa: N803
    attr = get_by_name(DataFrame.attributes, "width")
    assert isinstance(attr, Attribute)
    set_markdown(attr)
    assert attr.type.markdown == "int"


def test_iter_merged_parameters(DataFrame: Class):  # noqa: N803
    func = get_by_name(DataFrame.functions, "pipe")
    assert isinstance(func, Function)
    params = get_by_type(func.doc.sections, Parameters)
    assert params
    x = params.items
    assert x[0].name.str == "function"
    set_markdown(func)
    assert "typing.Callable][[Concatenate][__mkapi__" in x[0].type.markdown
    assert x[1].name.str == "*args"
    assert "[P][__mkapi_" in x[1].type.markdown
    assert x[2].name.str == "**kwargs"


def test_see_also(DataFrame: Class):  # noqa: N803
    func = get_by_name(DataFrame.functions, "head")
    assert isinstance(func, Function)
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    set_markdown(func)
    assert "[__mkapi__.polars.dataframe.frame.DataFrame.tail]" in see.text.markdown
    func = get_by_name(DataFrame.functions, "_read_csv")
    assert isinstance(func, Function)
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    set_markdown(func)
    assert "[__mkapi__.polars.io.csv.functions.read_csv]" in see.text.markdown


def test_see_also_text():
    name = "polars.lazyframe.frame"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    assert module
    cls = get_by_name(module.classes, "LazyFrame")
    assert isinstance(cls, Class)
    attr = get_by_name(cls.attributes, "dtypes")
    assert attr
    see = get_by_type(attr.doc.sections, SeeAlso)
    assert see
    set_markdown(attr)
    m = see.text.markdown
    assert "[schema][__mkapi__.polars.lazyframe.frame.LazyFrame.schema]" in m
    assert "Returns a" in m
    func = get_by_name(cls.functions, "deserialize")
    assert func
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    set_markdown(func)
    m = see.text.markdown
    assert "[__mkapi__.polars.lazyframe.frame.LazyFrame.serialize]" in m
    name = "polars.io.csv.functions"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    assert module
    func = get_by_name(module.functions, "read_csv")
    assert func
    see = get_by_type(func.doc.sections, SeeAlso)
    assert see
    set_markdown(func)
    m = see.text.markdown
    assert "[__mkapi__.polars.io.csv.functions.scan_csv]" in m


def test_property():
    name = "polars.dataframe.frame"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    cls = get_by_name(module.classes, "DataFrame")
    assert isinstance(cls, Class)
    assert not get_by_name(cls.functions, "plot")
    assert get_by_name(cls.attributes, "plot")


def test_overload():
    name = "polars.functions.repeat"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    assert len(list(iter_by_name(module.functions, "repeat"))) == 1
    func = get_by_name(module.functions, "repeat")
    assert isinstance(func, Function)
    assert func.doc.sections


def test_resolve():
    assert resolve("polars.DataFrame") == "polars.dataframe.frame.DataFrame"
    assert resolve("polars.DataType") == "polars.datatypes.classes.DataType"
    assert resolve("polars.col") == "polars.functions.col"
    assert resolve("polars.row") is None


def test_get_fullname():
    x = get_fullname("DataType", "polars.dataframe.frame")
    assert x == "polars.datatypes.classes.DataType"
    assert get_fullname("exceptions", "polars") != "polars.exceptions"
    assert get_fullname("api", "polars") == "polars.api"


def test_get_all():
    x = get_all("polars")
    assert x["api"] == "polars.api"
    assert x["ArrowError"] == "polars.exceptions.ArrowError"


# LazyFrame.tail


def test_create_module():
    name = "polars"
    assert create_module(name)
