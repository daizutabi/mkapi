from markdown import Markdown

from mkapi.pages import Page

source = """
# Title

## ![mkapi](a.o.Object|a|b)

text

### ![mkapi](a.s.Section)

end
"""


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
