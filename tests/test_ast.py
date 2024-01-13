import ast

from mkapi.ast import (
    StringTransformer,
    _iter_identifiers,
    iter_raises,
    unparse,
)


def _ast(src: str) -> ast.expr:
    expr = ast.parse(src).body[0]
    assert isinstance(expr, ast.Expr)
    return expr.value


def _unparse(src: str) -> str:
    return StringTransformer().unparse(_ast(src))


def test_expr_name():
    assert _unparse("a") == "__mkapi__.a"


def test_expr_subscript():
    assert _unparse("a[b]") == "__mkapi__.a[__mkapi__.b]"


def test_expr_attribute():
    assert _unparse("a.b") == "__mkapi__.a.b"
    assert _unparse("a.b.c") == "__mkapi__.a.b.c"
    assert _unparse("a().b[0].c()") == "__mkapi__.a().b[0].c()"
    assert _unparse("a(b.c[d])") == "__mkapi__.a(__mkapi__.b.c[__mkapi__.d])"


def test_expr_str():
    assert _unparse("list['X.Y']") == "__mkapi__.list[__mkapi__.X.Y]"


def test_iter_identifiers():
    x = list(_iter_identifiers("x, __mkapi__.a.b0[__mkapi__.c], y"))
    assert len(x) == 5
    assert x[0] == ("x, ", False)
    assert x[1] == ("a.b0", True)
    assert x[2] == ("[", False)
    assert x[3] == ("c", True)
    assert x[4] == ("], y", False)
    x = list(_iter_identifiers("__mkapi__.a.b()"))
    assert len(x) == 2
    assert x[0] == ("a.b", True)
    assert x[1] == ("()", False)
    x = list(_iter_identifiers("'ab'\n __mkapi__.a"))
    assert len(x) == 2
    assert x[0] == ("'ab'\n ", False)
    assert x[1] == ("a", True)
    x = list(_iter_identifiers("'ab'\n __mkapi__.α.β.γ"))  # noqa: RUF001
    assert len(x) == 2
    assert x[0] == ("'ab'\n ", False)
    assert x[1] == ("α.β.γ", True)  # noqa: RUF001


def test_unparse():
    def callback(s: str) -> str:
        return f"<{s}>"

    def f(s: str) -> str:
        return unparse(_ast(s), callback)

    assert f("a") == "<a>"
    assert f("a.b.c") == "<a.b.c>"
    assert f("a.b[c].d(e)") == "<a.b>[<c>].d(<e>)"
    assert f("a | b.c | d") == "<a> | <b.c> | <d>"
    assert f("list[A]") == "<list>[<A>]"
    assert f("list['A']") == "<list>[<A>]"


def test_iter_raises():
    src = "def f():\n raise ValueError('a')\n raise ValueError\n"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    raises = list(iter_raises(node))
    assert len(raises) == 1
    assert isinstance(raises[0].exc, ast.Call)
