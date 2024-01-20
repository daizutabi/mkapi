from pathlib import Path

from markdown import Markdown

from mkapi.objects import Class
from mkapi.pages import Page, create_page, object_paths, split_markdown

source = """
# Title
## ::: a.o.Object|a|b
text
### ::: a.s.Section
::: a.module|m
end
"""


def test_split_markdown():
    x = list(split_markdown(source))
    assert x[0] == ("# Title", -1, [])
    assert x[1] == ("a.o.Object", 2, ["a", "b"])
    assert x[2] == ("text", -1, [])
    assert x[3] == ("a.s.Section", 3, [])
    assert x[4] == ("a.module", 0, ["m"])
    assert x[5] == ("end", -1, [])


def test_page(tmpdir):
    object_paths.clear()
    name = "mkapi.objects.**, mkapi.items.*"
    path = Path(tmpdir / "a.md")
    create_page(name, path, 1, ["f", "g"])
    path = tmpdir.mkdir("src") / "b.md"
    page = Page("# Title\n::: mkapi.objects.Class", path)
    x = page.convert_markdown()
    assert "<!-- mkapi:begin[0] -->" in x
    assert "<!-- mkapi:end -->" in x
    assert "[Callable](../a.md#mkapi.objects.Callable)" in x
    assert "list[[Base](../a.md#mkapi.items.Base)]" in x
