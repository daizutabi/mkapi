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


def test_create_page(tmpdir):
    object_paths.clear()
    name = "mkapi.objects.**, mkapi.items.*"
    path = Path(tmpdir / "a.md")
    create_page(name, path, 1, ["f", "g"])
    path = tmpdir.mkdir("src") / "b.md"
    page = Page("# Title\n::: mkapi.objects.Class", path)
    markdown = page.convert_markdown()
    assert "<!-- mkapi:begin[0] -->" in markdown
    assert "<!-- mkapi:end -->" in markdown
    assert "[Callable](../a.md#mkapi.objects.Callable)" in markdown
    assert "list[[Base](../a.md#mkapi.items.Base)]" in markdown


def test_set_html(tmpdir):
    object_paths.clear()
    name = "polars,polars.dataframe"
    path = Path(tmpdir / "a.md")
    create_page(name, path, 1, ["f", "g"])
    name = "polars.datatypes.classes.*"
    path = Path(tmpdir / "b.md")
    create_page(name, path, 1, ["f", "g"])
    path = tmpdir.mkdir("src") / "c.md"
    page = Page("# Title\n::: polars.dataframe.frame.DataFrame", path)
    x = page.convert_markdown()
    assert "[polars](../a.md#polars).[dataframe](../a.md#polars.dataframe).frame" in x
    assert "[DataType](../b.md#polars.datatypes.classes.DataType)" in x
    html = Markdown().convert(x)
    html = page.convert_html(html, lambda *_: "")
    assert len(page.objects) == 1
    obj = page.objects[0]
    assert isinstance(obj, Class)
    x = obj.doc.type.html
    assert '<a href="../a.md#polars">polars</a>.' in x
    assert '<a href="../a.md#polars.dataframe">dataframe</a>' in x
    assert ".frame.DataFrame" in x
    object_paths.clear()
