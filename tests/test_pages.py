from markdown import Markdown

from mkapi.objects import Class, iter_types
from mkapi.pages import Page, _iter_markdown

source = """
# Title
## ::: a.o.Object|a|b
text
### ::: a.s.Section
::: a.module|m
end
"""


def test_iter_markdown():
    x = list(_iter_markdown(source))
    assert x[0] == ("# Title", -1, [])
    assert x[1] == ("a.o.Object", 2, ["a", "b"])
    assert x[2] == ("text", -1, [])
    assert x[3] == ("a.s.Section", 3, [])
    assert x[4] == ("a.module", 0, ["m"])
    assert x[5] == ("end", -1, [])


def callback_markdown(name, level, filters):
    f = "|".join(filters)
    return f"<{name}>[{level}]({f})"


def test_convert_markdown():
    abs_src_path = "/examples/docs/tutorial/index.md"
    abs_api_paths = [
        "/examples/docs/api/mkapi.md",
        "/examples/docs/api/mkapi.items.md",
    ]
    page = Page("::: mkapi.items.Parameters", abs_src_path, abs_api_paths)
    x = page.convert_markdown()
    assert "<!-- mkapi:begin[0] -->" in x
    assert "<!-- mkapi:end -->" in x
    assert "[Section](../api/mkapi.items.md#mkapi.items.Section)" in x
    assert "[Item](../api/mkapi.items.md#mkapi.items.Item) | None" in x
    assert "[mkapi](../api/mkapi.md#mkapi).[items]" in x
    assert "list[[Parameter](../api/mkapi.items.md" in x
    page = Page("::: mkapi.items.Parameters", "", [])
    x = page.convert_markdown()
    assert "../api/mkapi.items" not in x


def test_convert_html():
    abs_src_path = "/examples/docs/tutorial/index.md"
    abs_api_paths = [
        "/examples/docs/api/mkapi.md",
        "/examples/docs/api/mkapi.items.md",
    ]
    page = Page("::: mkapi.items.Parameters", abs_src_path, abs_api_paths)
    markdown = page.convert_markdown()
    converter = Markdown()
    html = converter.convert(markdown)
    page.convert_html(html)
    obj = page.objects[0]
    assert isinstance(obj, Class)
    x = "\n".join(x.html for x in iter_types(obj))
    assert '<p><a href="../api/mkapi.items.md#mkapi.items.Item">Item</a>' in x
