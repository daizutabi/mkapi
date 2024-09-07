import ast
import textwrap
from inspect import _ParameterKind


def test_iter_child_nodes():
    from mkapi.ast import iter_child_nodes

    src = "a:int\nb=1\n'''b'''\nc='c'"
    node = ast.parse(src)
    x = list(iter_child_nodes(node))
    assert len(x) == 3
    assert x[0].__doc__ is None
    assert x[1].__doc__ == "b"
    assert x[2].__doc__ is None


def test_iter_parameters():
    from mkapi.ast import iter_parameters

    src = "def f(): pass"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    assert list(iter_parameters(node)) == []
    src = "def f(a,/,b=1,*,c,d=1): pass"
    node = ast.parse(src).body[0]
    assert isinstance(node, ast.FunctionDef)
    x = list(iter_parameters(node))
    assert x[0].name == "a"
    assert x[1].name == "b"
    assert x[2].name == "c"
    assert x[3].name == "d"
    assert x[0].default is None
    assert x[1].default is not None
    assert x[2].default is None
    assert x[3].default is not None
    assert x[0].kind is _ParameterKind.POSITIONAL_ONLY
    assert x[1].kind is _ParameterKind.POSITIONAL_OR_KEYWORD
    assert x[2].kind is _ParameterKind.KEYWORD_ONLY
    assert x[3].kind is _ParameterKind.KEYWORD_ONLY


def test_iter_raises():
    from mkapi.ast import iter_raises

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
    from mkapi.ast import StringTransformer

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
    from mkapi.ast import _iter_identifiers

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
    x = list(_iter_identifiers("'ab'\n __mkapi__.α.β.γ"))
    assert len(x) == 2
    assert x[0] == ("'ab'\n ", False)
    assert x[1] == ("α.β.γ", True)


def test_unparse():
    from mkapi.ast import unparse

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


def test_is_classmethod():
    from mkapi.ast import is_classmethod

    src = "@classmethod\ndef func(cls): pass"
    node = ast.parse(src).body[0]
    assert is_classmethod(node)
    src = "def func(cls): pass"
    node = ast.parse(src).body[0]
    assert not is_classmethod(node)


def test_is_staticmethod():
    from mkapi.ast import is_staticmethod

    src = "@staticmethod\ndef func(): pass"
    node = ast.parse(src).body[0]
    assert is_staticmethod(node)
    src = "def func(): pass"
    node = ast.parse(src).body[0]
    assert not is_staticmethod(node)


def test_is_assign():
    from mkapi.ast import is_assign

    src = "x: int = 5"
    node = ast.parse(src).body[0]
    assert is_assign(node)
    src = "x = 5"
    node = ast.parse(src).body[0]
    assert is_assign(node)
    src = "def func(): pass"
    node = ast.parse(src).body[0]
    assert not is_assign(node)


def test_is_function_def():
    from mkapi.ast import is_function_def

    src = "def func(): pass"
    node = ast.parse(src).body[0]
    assert is_function_def(node)
    src = "class MyClass: pass"
    node = ast.parse(src).body[0]
    assert not is_function_def(node)


def test_is_property():
    from mkapi.ast import is_property

    src = "@property\ndef func(self): pass"
    node = ast.parse(src).body[0]
    assert is_property(node)
    src = "def func(self): pass"
    node = ast.parse(src).body[0]
    assert not is_property(node)


def test_is_setter():
    from mkapi.ast import is_setter

    src = "@property\n@func.setter\ndef func(self, value): pass"
    node = ast.parse(src).body[0]
    assert is_setter(node)
    src = "def func(self, value): pass"
    node = ast.parse(src).body[0]
    assert not is_setter(node)


def test_has_decorator():
    from mkapi.ast import has_decorator

    src = "@my_decorator\ndef func(): pass"
    node = ast.parse(src).body[0]
    assert has_decorator(node, "my_decorator")
    assert not has_decorator(node, "other_decorator")


def test_iter_child_nodes_import():
    from mkapi.ast import iter_child_nodes

    src = """
    import os
    class MyClass:
        def method(self): pass
    """
    node = ast.parse(textwrap.dedent(src))
    children = list(iter_child_nodes(node))
    assert len(children) == 2
    assert isinstance(children[0], ast.Import)
    assert isinstance(children[1], ast.ClassDef)
