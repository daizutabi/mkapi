from pathlib import Path

from markdown import Markdown

from mkapi.objects import Class, iter_types
from mkapi.pages import Page, _iter_markdown, collect_objects

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
    collect_objects("mkapi.items", Path("/x/api/a.md"))
    abs_src_path = "/b.md"
    page = Page("::: mkapi.items.Parameters", abs_src_path)
    x = page.convert_markdown()
    assert "<!-- mkapi:begin[0] -->" in x
    assert "<!-- mkapi:end -->" in x
    assert "[Section](x/api/a.md#mkapi.items.Section)" in x
