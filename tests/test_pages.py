from markdown import Markdown

from mkapi.pages import _iter_markdown, convert_html, convert_markdown

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
    x = convert_markdown(source, callback_markdown)
    assert "# Title\n\n" in x
    assert "<!-- mkapi:begin[0] -->\n<a.o.Object>[2](a|b)\n<!-- mkapi:end -->\n\n" in x
    assert "\n\ntext\n\n" in x
    assert "<!-- mkapi:begin[1] -->\n<a.s.Section>[3]()\n<!-- mkapi:end -->\n\n" in x
    assert "<!-- mkapi:begin[2] -->\n<a.module>[0](m)\n<!-- mkapi:end -->\n\n" in x


def callback_html(index, html):
    return f"<X>{index}{html[:10]}</X>"


def test_convert_html():
    markdown = convert_markdown(source, callback_markdown)
    converter = Markdown()
    html = converter.convert(markdown)
    assert "<h1>Title</h1>\n" in html
    assert "<!-- mkapi:begin[0] -->\n" in html
    assert '<p><a.o.Object><a href="a|b">2</a></p>' in html
    assert '<p><a.s.Section><a href="">3</a></p>' in html
    assert '<p><a.module><a href="m">0</a></p>' in html
    html = convert_html(html, callback_html)
    assert "<h1>Title</h1>\n" in html
    assert "<X>0<p><a.o.Ob</X>\n\n" in html
    assert "<X>1<p><a.s.Se</X>\n\n" in html
    assert "<X>2<p><a.modu</X>\n\n" in html


def test_page():
    abs_src_path = "/examples/docs/tutorial/index.md"
    abs_api_paths = [
        "/examples/docs/api/a.o.md",
        "/examples/docs/api/a.s.md",
    ]
    # page = Page(source, abs_src_path, abs_api_paths)
    # m = page.convert_markdown()
    # print(m)
    # assert m.startswith("# Title\n")
    # assert "<!-- mkapi:begin:a.o.Object:[a|b] -->" in m
    # assert "## [a.o](../api/a.o.md#mkapi.core).[base]" in m
    # assert "<!-- mkapi:begin:1:[strict] -->" in m
    # assert "[mkapi.core.base](../api/mkapi.core.base.md#mkapi.core.base)." in m
    # assert "[Base](../api/mkapi.core.base.md#mkapi.core.base.Base)" in m
    # assert "\n###" in m
    # assert "\n####" in m
    # assert m.endswith("end")

    # converter = Markdown()
    # h = page.convert_html(converter.convert(m))
    # assert "<h1>Title</h1>" in h
    # print("-" * 40)
    # print(h)
    # assert 0
    # assert '<div class="mkapi-node" id="mkapi.core.base">' in h
    # assert '<a href="../api/mkapi.core.md#mkapi.core">MKAPI.CORE</a>' in h
    # assert '<a href="../api/mkapi.core.base.md#mkapi.core.base">BASE</a>' in h
    # assert '<a href="#mkapi.core.base.Base">Base</a>' in h
    # assert '<div class="mkapi-node" id="mkapi.core.base.Base">' in h
    # assert '<div class="mkapi-object dataclass code top">' in h
    # assert '<a href="../api/mkapi.core.base.md#mkapi.core.base">mkapi.core.base' in h
    # assert '<a href="../api/mkapi.core.base.md#mkapi.core.base.Base">Base</a>' in h
    # assert '<span class="mkapi-section-name-body attributes">Attributes</span>' in h
    # assert '<span class="mkapi-section-name-body methods">Methods</span>' in h
    # assert '<span class="mkapi-section-name-body classes">Classes</span>' in h
    # assert "<p>end</p>" in h
