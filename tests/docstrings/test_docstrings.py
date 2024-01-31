import ast

from mkapi.docstrings import parse
from mkapi.markdown import convert
from mkapi.utils import get_by_name, get_module_node


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
    print(src)
    doc = parse(src)
    s = get_by_name(doc.sections, "Parameters")
    assert s
    i = get_by_name(s.items, "streaming")
    assert i
    assert i.text.str
    print(i.text.str)
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
    m = convert(src)
    print(m)
    doc = parse(src)
    for s in doc.sections:
        print("--" * 40)
        print(s.text.str)
        print("--" * 40)
    assert 0


# polars.dataframe.frame.DataFrame.write_delta  `here_`
# polars.dataframe.frame.DataFrame.map_rows
