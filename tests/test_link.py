from mkapi.link import get_markdown_from_name, get_markdown_from_type, get_markdown_from_type_string


def test_get_link_from_type():
    x = get_markdown_from_type("mkapi.objects", "Object")
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_markdown_from_type("mkapi.objects", "Object.__repr__")
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.objects.Object.__repr__]" in x
    x = get_markdown_from_type("mkapi.plugins", "MkDocsPage")
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"
    x = get_markdown_from_type("mkdocs.plugins", "jinja2.Template")
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x
    x = get_markdown_from_type("polars", "DataFrame")
    assert x == "[DataFrame][__mkapi__.polars.dataframe.frame.DataFrame]"
    assert get_markdown_from_type("mkapi.objects", "str") == "str"
    assert get_markdown_from_type("mkapi.objects", "None") == "None"


def test_get_link_from_type_string():
    f = get_markdown_from_type_string
    x = f("mkapi.objects", "1 Object or Class.")
    assert "1 [Object][__mkapi__.mkapi.objects.Object] " in x
    assert "or [Class][__mkapi__.mkapi.objects.Class]." in x
