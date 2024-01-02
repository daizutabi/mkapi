import ast

import pytest

from mkapi.ast.eval import StringTransformer, iter_identifiers
from mkapi.ast.node import Module, get_module, get_module_node


def _unparse(src: str) -> str:
    expr = ast.parse(src).body[0]
    assert isinstance(expr, ast.Expr)
    return StringTransformer().unparse(expr.value)


def test_parse_expr_name():
    assert _unparse("a") == "__mkapi__.a"


def test_parse_expr_subscript():
    assert _unparse("a[b]") == "__mkapi__.a[__mkapi__.b]"


def test_parse_expr_attribute():
    assert _unparse("a.b") == "__mkapi__.a.b"
    assert _unparse("a.b.c") == "__mkapi__.a.b.c"
    assert _unparse("a().b[0].c()") == "__mkapi__.a().b[0].c()"
    assert _unparse("a(b.c[d])") == "__mkapi__.a(__mkapi__.b.c[__mkapi__.d])"


def test_parse_expr_str():
    assert _unparse("list['X.Y']") == "__mkapi__.list[__mkapi__.X.Y]"


@pytest.fixture(scope="module")
def module():
    node = get_module_node("mkapi.ast.node")
    return get_module(node)


def test_iter_identifiers():
    x = list(iter_identifiers("x, __mkapi__.a.b0[__mkapi__.c], y"))
    assert len(x) == 5
    assert x[0] == ("x, ", False)
    assert x[1] == ("a.b0", True)
    assert x[2] == ("[", False)
    assert x[3] == ("c", True)
    assert x[4] == ("], y", False)
    x = list(iter_identifiers("__mkapi__.a.b()"))
    assert len(x) == 2
    assert x[0] == ("a.b", True)
    assert x[1] == ("()", False)
    x = list(iter_identifiers("'ab'\n __mkapi__.a"))
    assert len(x) == 2
    assert x[0] == ("'ab'\n ", False)
    assert x[1] == ("a", True)
    x = list(iter_identifiers("'ab'\n __mkapi__.α.β.γ"))  # noqa: RUF001
    assert len(x) == 2
    assert x[0] == ("'ab'\n ", False)
    assert x[1] == ("α.β.γ", True)  # noqa: RUF001


# def test_functions(module: Module):
#     func = module.functions._get_def_args  # noqa: SLF001
#     ann = func.args[0].annotation
#     assert isinstance(ann, ast.expr)
#     print(Transformer().unparse(ann))
#     print(Transformer().unparse(func.returns))
#     assert 0
