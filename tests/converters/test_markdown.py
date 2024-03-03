import ast
import re


def test_link_pattern():
    from mkapi.converters import LINK_PATTERN

    def f(m: re.Match) -> str:
        name = m.group(1)
        if name == "abc":
            return f"[{name}][_{name}]"
        return m.group()

    assert re.search(LINK_PATTERN, "X[abc]Y")
    assert not re.search(LINK_PATTERN, "X[ab c]Y")
    assert re.search(LINK_PATTERN, "X[abc][]Y")
    assert not re.search(LINK_PATTERN, "X[abc](xyz)Y")
    assert not re.search(LINK_PATTERN, "X[abc][xyz]Y")
    assert re.sub(LINK_PATTERN, f, "X[abc]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc[abc]]Y") == "X[abc[abc][_abc]]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab]Y") == "X[ab]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab c]Y") == "X[ab c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc] c]Y") == "X[abc][_abc] c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc](xyz)Y") == "X[abc](xyz)Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][xyz]Y") == "X[abc][xyz]Y"


def test_get_markdown_name_noreplace():
    from mkapi.converters import get_markdown_name

    x = get_markdown_name("abc")
    assert x == "[abc][__mkapi__.abc]"
    x = get_markdown_name("a_._b.c")
    assert r"[a\_][__mkapi__.a_]." in x
    assert r".[\_b][__mkapi__.a_._b]." in x
    assert ".[c][__mkapi__.a_._b.c]" in x


def test_get_markdown_name():
    from mkapi.converters import get_markdown_name
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.objects")

    x = get_markdown_name("Object", replace)
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_markdown_name("Object.__repr__", replace)
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.objects.Object.__repr__]" in x

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.plugins")

    x = get_markdown_name("MkDocsPage", replace)
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkdocs.plugins")

    x = get_markdown_name("jinja2.Template", replace)
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x

    assert get_markdown_name("str", replace) == "str"
    assert get_markdown_name("None", replace) == "None"
    assert get_markdown_name("_abc", replace) == "\\_abc"


def test_get_markdown_str():
    from mkapi.converters import get_markdown_str
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.objects")

    type_string = "1 Object or Class."
    x = get_markdown_str(type_string, replace)
    assert "1 [Object][__mkapi__.mkapi.objects.Object] " in x
    assert "or [Class][__mkapi__.mkapi.objects.Class]." in x


def test_get_markdown_expr():
    from mkapi.converters import get_markdown_expr
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.converters")

    expr = ast.parse("re.Match[Converter](Replace)").body[0].value  # type: ignore
    assert isinstance(expr, ast.expr)
    x = get_markdown_expr(expr, replace)
    assert x.startswith("[re][__mkapi__.re].[Match][__mkapi__.re.Match]")
    assert "[[Converter][__mkapi__.mkapi.converters.Converter]]" in x
    assert x.endswith("([Replace][__mkapi__.mkapi.converters.Replace])")


def test_get_markdown_expr_constant():
    from mkapi.converters import get_markdown_expr
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.converters")

    expr = ast.Constant("re.Match")
    assert isinstance(expr, ast.expr)
    x = get_markdown_expr(expr, replace)
    assert x == "[re][__mkapi__.re].[Match][__mkapi__.re.Match]"

    expr = ast.Constant(123)
    assert isinstance(expr, ast.expr)
    x = get_markdown_expr(expr, replace)
    assert x == "123"


def test_get_markdown_text_module_objects():
    from mkapi.converters import get_markdown_text
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.objects")

    x = get_markdown_text("Class", replace)
    assert x == "Class"
    x = get_markdown_text("a [Class] b", replace)
    assert x == "a [Class][__mkapi__.mkapi.objects.Class] b"
    x = get_markdown_text("a [Class][] b", replace)
    assert x == "a [Class][__mkapi__.mkapi.objects.Class] b"
    x = get_markdown_text("a [Class][a] b", replace)
    assert x == "a [Class][a] b"
    m = "a \n```\n[Class][a]\n```\n b"
    assert get_markdown_text(m, replace) == m


def test_get_markdown_text_module_plugins():
    from mkapi.converters import get_markdown_text
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.plugins")

    x = get_markdown_text("a [MkAPIPlugin][] b", replace)
    assert x == "a [MkAPIPlugin][__mkapi__.mkapi.plugins.MkAPIPlugin] b"
    x = get_markdown_text("a [BasePlugin][] b", replace)
    assert x == "a [BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin] b"
    x = get_markdown_text("a [MkDocsConfig][] b", replace)
    assert x == "a [MkDocsConfig][__mkapi__.mkdocs.config.defaults.MkDocsConfig] b"

    x = get_markdown_text("a [__mkapi__.b] c", replace)
    assert x == "a b c"
    x = get_markdown_text("a [b] c", replace)
    assert x == "a [b] c"
