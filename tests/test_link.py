from mkapi.globals import get_fullname
from mkapi.link import get_markdown, get_markdown_from_type_string


def test_get_markdown():
    x = get_markdown("abc")
    assert x == "[abc][__mkapi__.abc]"
    x = get_markdown("a_._b.c")
    assert r"[a\_][__mkapi__.a_]." in x
    assert r".[\_b][__mkapi__.a_._b]." in x
    assert ".[c][__mkapi__.a_._b.c]" in x


def test_get_markdown_from_fullname_replace():
    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname("mkapi.objects", name)

    x = get_markdown("Object", replace)
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_markdown("Object.__repr__", replace)
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.objects.Object.__repr__]" in x

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname("mkapi.plugins", name)

    x = get_markdown("MkDocsPage", replace)
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"

    def replace(name: str) -> str | None:
        return get_fullname("mkdocs.plugins", name)

    x = get_markdown("jinja2.Template", replace)
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x

    assert get_markdown("str", replace) == "str"
    assert get_markdown("None", replace) == "None"
    assert get_markdown("_abc", replace) == "_abc"


def test_get_markdown_from_type_string():
    def replace(name: str) -> str | None:
        return get_fullname("mkapi.objects", name)

    source = "1 Object or Class."
    x = get_markdown_from_type_string(source, replace)
    assert "1 [Object][__mkapi__.mkapi.objects.Object] " in x
    assert "or [Class][__mkapi__.mkapi.objects.Class]." in x
