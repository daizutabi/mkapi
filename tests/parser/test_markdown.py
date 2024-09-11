import ast

import pytest


@pytest.mark.parametrize(
    "text",
    [
        "`abc`",
        "`abc[abc]`",
        "```abc```",
        "`` `abc` ``",
    ],
)
def test_code_pattern_match(text):
    from mkapi.parser import CODE_PATTERN

    m = CODE_PATTERN.match(text)
    assert m
    assert m.group() == text


def test_get_markdown_name_noreplace():
    from mkapi.parser import get_markdown_name

    x = get_markdown_name("abc")
    assert x == "[abc][__mkapi__.abc]"
    x = get_markdown_name("a_._b.c")
    assert r"[a\_][__mkapi__.a_]." in x
    assert r".[\_b][__mkapi__.a_._b]." in x
    assert ".[c][__mkapi__.a_._b.c]" in x


def test_get_markdown_name():
    from mkapi.node import get_fullname_from_module
    from mkapi.parser import get_markdown_name

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname_from_module(name, "mkapi.object")

    x = get_markdown_name("Object", replace)
    assert x == "[Object][__mkapi__.mkapi.object.Object]"
    x = get_markdown_name("Object.__repr__", replace)
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.object.Object.__repr__]" in x

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname_from_module(name, "mkapi.plugin")

    x = get_markdown_name("MkDocsPage", replace)
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"

    def replace(name: str) -> str | None:
        return get_fullname_from_module(name, "mkdocs.plugins")

    x = get_markdown_name("jinja2.Template", replace)
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x

    assert get_markdown_name("str", replace) == "str"
    assert get_markdown_name("None", replace) == "None"
    assert get_markdown_name("_abc", replace) == "\\_abc"


def test_get_markdown_str():
    from mkapi.node import get_fullname_from_module
    from mkapi.parser import get_markdown_str

    def replace(name: str) -> str | None:
        return get_fullname_from_module(name, "mkapi.object")

    type_string = "1 Object or Class."
    x = get_markdown_str(type_string, replace)
    assert "1 [Object][__mkapi__.mkapi.object.Object] " in x
    assert "or [Class][__mkapi__.mkapi.object.Class]." in x


def test_get_markdown_expr():
    from mkapi.node import get_fullname_from_module
    from mkapi.parser import get_markdown_expr

    def replace(name: str) -> str | None:
        return get_fullname_from_module(name, "mkapi.markdown")

    expr = ast.parse("re.Match[finditer](sub)").body[0].value  # type: ignore
    assert isinstance(expr, ast.expr)
    x = get_markdown_expr(expr, replace)
    assert x.startswith("[re][__mkapi__.re].[Match][__mkapi__.re.Match]")
    print(x)
    assert "[[finditer][__mkapi__.mkapi.markdown.finditer]]" in x
    assert x.endswith("([sub][__mkapi__.mkapi.markdown.sub])")


def test_get_markdown_expr_constant():
    from mkapi.node import get_fullname_from_module
    from mkapi.parser import get_markdown_expr

    def replace(name: str) -> str | None:
        return get_fullname_from_module(name, "mkapi.markdown")

    expr = ast.Constant("re.Match")
    assert isinstance(expr, ast.expr)
    x = get_markdown_expr(expr, replace)
    assert x == "[re][__mkapi__.re].[Match][__mkapi__.re.Match]"

    expr = ast.Constant(123)
    assert isinstance(expr, ast.expr)
    x = get_markdown_expr(expr, replace)
    assert x == "123"


def test_get_markdown_text_module_objects():
    from mkapi.node import get_fullname_from_module
    from mkapi.parser import get_markdown_text

    def replace(name: str) -> str | None:
        return get_fullname_from_module(name, "mkapi.object")

    x = get_markdown_text("Class", replace)
    assert x == "Class"
    x = get_markdown_text("a `Class` b", replace)
    assert x == "a [`Class`][__mkapi__.mkapi.object.Class] b"
    x = get_markdown_text("a `Class ` b", replace)
    assert x == "a `Class ` b"
    x = get_markdown_text("a `invalid` b", replace)
    assert x == "a `invalid` b"
    x = get_markdown_text("a `` `Class` `` b", replace)
    assert x == "a `` `Class` `` b"
    m = "a \n```\n`Class`\n```\n b"
    assert get_markdown_text(m, replace) == m


def test_get_markdown_text_module_plugins():
    from mkapi.node import get_fullname_from_module
    from mkapi.parser import get_markdown_text

    def replace(name: str) -> str | None:
        return get_fullname_from_module(name, "mkapi.plugin")

    x = get_markdown_text("a `MkApiPlugin` b", replace)
    assert x == "a [`MkApiPlugin`][__mkapi__.mkapi.plugin.MkApiPlugin] b"
    x = get_markdown_text("a `BasePlugin` b", replace)
    assert x == "a [`BasePlugin`][__mkapi__.mkdocs.plugins.BasePlugin] b"
    x = get_markdown_text("a `MkDocsConfig` b", replace)
    assert x == "a [`MkDocsConfig`][__mkapi__.mkdocs.config.defaults.MkDocsConfig] b"
    x = get_markdown_text("a [b] c", replace)
    assert x == "a [b] c"
