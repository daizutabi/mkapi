from pathlib import Path

from mkapi import renderers
from mkapi.pages import _split_markdown, create_markdown, create_page, object_paths

source = """
# Title
## ::: a.o.Object|a|b
text
### ::: a.s.Section
::: a.module|m
end
"""


def test_split_markdown():
    x = list(_split_markdown(source))
    assert x[0] == ("# Title", -1, [])
    assert x[1] == ("a.o.Object", 2, ["a", "b"])
    assert x[2] == ("text", -1, [])
    assert x[3] == ("a.s.Section", 3, [])
    assert x[4] == ("a.module", 0, ["m"])
    assert x[5] == ("end", -1, [])


def test_create_page(tmpdir):
    object_paths.clear()
    name = "mkapi.objects.**, mkapi.items.*"
    path = Path(tmpdir / "a.md")
    create_page(name, path, ["f", "g"])
    path = tmpdir.mkdir("src") / "b.md"
    # page = Page("# Title\n::: mkapi.objects.Class", path)
    # markdown = page.convert_markdown()
    # assert "<!-- mkapi:begin[0] -->" in markdown
    # assert "<!-- mkapi:end -->" in markdown
    # assert "[Callable](../a.md#mkapi.objects.Callable)" in markdown
    # assert "list[[Base](../a.md#mkapi.items.Base)]" in markdown


def test_create_markdown():
    renderers.load_templates()
    name = "polars.dataframe._html.Tag"
    m = create_markdown(name, 1, [])
    print(m)
