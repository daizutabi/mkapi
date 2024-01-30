import ast
import inspect
import re

from mkapi.docstrings import URL_PATTERN, parse, preprocess
from mkapi.utils import get_by_name, get_module_node


def test_url_pattern():
    def f(x):
        return re.sub(URL_PATTERN, r" <\1>\2", x)

    x = " https://a.b.c"
    assert f(x) == " <https://a.b.c>"
    x = "a https://a.b.c."
    assert f(x) == "a <https://a.b.c>."
    x = "a https://a.b.c. b"
    assert f(x) == "a <https://a.b.c>. b"


def test_preprocess():
    src = """
    `abc <def>`_
    :func:`ghi <jkl>`
    :func:`mno`
    abc  # doctest: XYZ
    def
    """
    src = inspect.cleandoc(src)
    lines = preprocess(src).split("\n")
    assert lines[0] == "[abc](def)"
    assert lines[1] == "[ghi][__mkapi__.jkl]"
    assert lines[2] == "[__mkapi__.mno][]"
    assert lines[3] == "abc"


def get(module: str, n1: str, n2: str | None) -> str:
    t = ast.ClassDef | ast.FunctionDef
    node = get_module_node(module)
    assert node
    nodes = [n for n in ast.iter_child_nodes(node) if isinstance(n, t)]
    node = get_by_name(nodes, n1)
    assert node
    if not n2:
        src = ast.get_docstring(node)
        assert src
        return src
    nodes = [n for n in ast.iter_child_nodes(node) if isinstance(n, t)]
    node = get_by_name(nodes[::-1], n2)
    assert node
    src = ast.get_docstring(node)
    assert src
    return src


def test_polars_collect():
    src = get("polars.lazyframe.frame", "LazyFrame", "collect")
    doc = parse(src)
    s = get_by_name(doc.sections, "Parameters")
    assert s
    i = get_by_name(s.items, "streaming")
    assert i
    assert i.text.str
    assert "!!! warning\n    This functionality" in i.text.str


def test_polars_from_numpy():
    src = get("polars.convert", "from_numpy", None)
    doc = parse(src)
    s = get_by_name(doc.sections, "Parameters")
    assert s
    i = get_by_name(s.items, "data")
    assert i
    assert i.type.expr
    assert ast.unparse(i.type.expr) == "'numpy.ndarray'"


def test_polars_a():
    src = get("polars.dataframe.frame", "DataFrame", "group_by_dynamic")
    print(src)
    doc = parse(src)
    print(doc.sections[-2].text.str)
    assert 0
