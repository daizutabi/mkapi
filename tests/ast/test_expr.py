import ast

import pytest

from mkapi.ast.expr import parse_expr


def _expr(src: str) -> str:
    expr = ast.parse(src).body[0]
    assert isinstance(expr, ast.Expr)
    return parse_expr(expr.value)


@pytest.mark.parametrize("x", ["1", "'a'", "...", "None", "True"])
def test_parse_expr_constant(x):
    assert _expr(x) == x


@pytest.mark.parametrize("x", ["()", "(1,)", "(1, 2)"])
def test_parse_expr_tuple(x):
    assert _expr(x.replace(" ", "")) == x


@pytest.mark.parametrize("x", ["[]", "[1]", "[1, 2]"])
def test_parse_expr_list(x):
    assert _expr(x.replace(" ", "")) == x


def test_parse_expr_attribute():
    assert _expr("a.b.c") == "a.b.c"


@pytest.mark.parametrize("x", ["1:2", "1:", ":-2", "1:10:2", "1::2", "::3", ":3:2"])
def test_parse_expr_slice(x):
    x = f"a[{x}]"
    assert _expr(x) == x


def test_parse_expr_subscript():
    assert _expr("a[1]") == "a[1]"
    assert _expr("a[1,2.0,'c']") == "a[1, 2.0, 'c']"


def test_parse_expr_call():
    assert _expr("f()") == "f()"
    assert _expr("f(a)") == "f(a)"
    assert _expr("f(a,b=c(),*d,**e[1])") == "f(a, *d, b=c(), **e[1])"


def test_callback():
    def callback(expr: ast.expr):
        if isinstance(expr, ast.Name):
            return f"<{expr.id}>"
        return None

    expr = ast.parse("a[b]").body[0]
    assert isinstance(expr, ast.Expr)
    assert parse_expr(expr.value, callback) == "<a>[<b>]"
    expr = ast.parse("a.b.c").body[0]
    assert isinstance(expr, ast.Expr)
    assert parse_expr(expr.value, callback) == "<a>.b.c"
    expr = ast.parse("a(1).b[c].d").body[0]
    assert isinstance(expr, ast.Expr)
    assert parse_expr(expr.value, callback) == "<a>(1).b[<c>].d"
