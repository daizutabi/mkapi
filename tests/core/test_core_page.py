from markdown import Markdown

from mkapi.core.page import Page

source = """
# Title

## ![mkapi](mkapi.core.base|upper|link)

text

### ![mkapi](mkapi.core.base.Base|strict)

end
"""


def test_page():
    abs_src_path = "/examples/docs/tutorial/index.md"
    abs_api_paths = [
        "/examples/docs/api/mkapi.core.md",
        "/examples/docs/api/mkapi.core.base.md",
    ]
    page = Page(source, abs_src_path, abs_api_paths)
    m = page.markdown
    assert m.startswith("# Title\n")
    assert "<!-- mkapi:begin:0:[upper|link] -->" in m
    assert "## [mkapi.core](../api/mkapi.core.md#mkapi.core).[base]" in m
    assert "<!-- mkapi:begin:1:[strict] -->" in m
    assert "[mkapi.core.base](../api/mkapi.core.base.md#mkapi.core.base)." in m
    assert "[Base](../api/mkapi.core.base.md#mkapi.core.base.Base)" in m
    assert "\n###" in m
    assert "\n####" in m
    assert m.endswith("end")

    converter = Markdown()
    h = page.content(converter.convert(m))
    assert "<h1>Title</h1>" in h
    assert '<div class="mkapi-node" id="mkapi.core.base">' in h
    assert '<a href="../api/mkapi.core.md#mkapi.core">MKAPI.CORE</a>' in h
    assert '<a href="../api/mkapi.core.base.md#mkapi.core.base">BASE</a>' in h
    assert '<a href="#mkapi.core.base.Base">Base</a>' in h
    assert '<div class="mkapi-node" id="mkapi.core.base.Base">' in h
    assert '<h3 class="mkapi-object mkapi-object-dataclass code">' in h
    assert '<a href="../api/mkapi.core.base.md#mkapi.core.base">mkapi.core.base' in h
    assert '<a href="../api/mkapi.core.base.md#mkapi.core.base.Base">Base</a>' in h
    assert '<span class="mkapi-section-name-body">Attributes</span>' in h
    assert '<span class="mkapi-section-name-body">Methods</span>' in h
    assert '<span class="mkapi-section-name-body">Classes</span>' in h
    assert "<p>end</p>" in h
