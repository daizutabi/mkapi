import ast
from inspect import _ParameterKind

from mkapi.ast import StringTransformer, _iter_identifiers, iter_child_nodes, iter_parameters, iter_raises, unparse


def test_iter_child_nodes():
    src = "a:int\nb=1\n'''b'''\nc='c'"
    node = ast.parse(src)
    x = list(iter_child_nodes(node))
    assert len(x) == 3
    assert x[0].__doc__ is None
    assert x[1].__doc__ == "b"
    assert x[2].__doc__ is None


def test_iter_parameters():
    src = "def f(): pass"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    assert list(iter_parameters(node)) == []
    src = "def f(a,/,b=1,*,c,d=1): pass"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    x = list(iter_parameters(node))
    assert x[0][-1] is _ParameterKind.POSITIONAL_ONLY
    assert x[1][-1] is _ParameterKind.POSITIONAL_OR_KEYWORD
    assert x[2][-1] is _ParameterKind.KEYWORD_ONLY
    assert x[3][-1] is _ParameterKind.KEYWORD_ONLY
    assert x[0][2] is None
    assert x[1][2] is not None
    assert x[2][2] is None
    assert x[3][2] is not None


def test_iter_raises():
    src = "def f():\n raise ValueError('a')\n raise ValueError\n"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    raises = list(iter_raises(node))
    assert len(raises) == 1


def _expr(src: str) -> ast.expr:
    expr = ast.parse(src).body[0]
    assert isinstance(expr, ast.Expr)
    return expr.value


def _unparse(src: str) -> str:
    return StringTransformer().unparse(_expr(src))


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
        return unparse(_expr(s), callback)

    assert f("a") == "<a>"
    assert f("a.b.c") == "<a.b.c>"
    assert f("a.b[c].d(e)") == "<a.b>[<c>].d(<e>)"
    assert f("a | b.c | d") == "<a> | <b.c> | <d>"
    assert f("list[A]") == "<list>[<A>]"
    assert f("list['A']") == "<list>[<A>]"
