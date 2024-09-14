import pytest

from mkapi.renderer import TemplateKind


def test_page_create_object():
    from mkapi.page import Page, PageKind

    p = Page.create_object("a/b/c.md", "x")
    assert p.src_uri == "a/b/c.md"
    assert p.name == "x"
    assert p.markdown == ""
    assert p.kind == PageKind.OBJECT
    assert p.is_object_page()
    assert not p.is_source_page()
    assert p.is_api_page()
    assert not p.is_documentation_page()


def test_page_create_source():
    from mkapi.page import Page, PageKind

    p = Page.create_source("a/b/c.md", "x")
    assert p.kind == PageKind.SOURCE
    assert not p.is_object_page()
    assert p.is_source_page()
    assert p.is_api_page()
    assert not p.is_documentation_page()


def test_page_create_documentation():
    from mkapi.page import Page, PageKind

    p = Page.create_documentation("a/b/c.md", "x")
    assert p.name == ""
    assert p.markdown == "x"
    assert p.kind == PageKind.DOCUMENTATION
    assert not p.is_object_page()
    assert not p.is_source_page()
    assert not p.is_api_page()
    assert p.is_documentation_page()


def test_page_repr():
    from mkapi.page import Page

    p = Page.create_source("a/b/c.md", "x")
    assert repr(p) == "Page('a/b/c.md')"


def test_generate_module_markdown():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("mkapi.doc")
    assert m.startswith("# ::: mkapi.doc\n")
    assert "\n## ::: Item mkapi.doc\n" in m
    assert "\n### ::: Item.clone mkapi.doc\n" in m
    assert "\n## ::: merge mkapi.doc\n" in m

    assert "mkapi.doc" in names
    assert "mkapi.doc.Item" in names
    assert "mkapi.doc.Item.clone" in names
    assert "mkapi.doc.merge" in names


def test_generate_module_markdown_export():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("jinja2")
    assert m.startswith("# ::: jinja2\n")
    assert "\n## ::: Template jinja2\n" in m
    assert "\n### ::: Template.render jinja2\n" in m


def test_generate_module_markdown_alias():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("example._styles")
    assert m.startswith("# ::: example._styles\n")
    assert "\n## ::: ExampleClassGoogle example._styles\n" in m
    assert "\n## ::: ExampleClassNumPy example._styles\n" in m

    assert "example._styles" in names
    assert "example._styles.ExampleClassGoogle" in names
    assert "example._styles.ExampleClassNumPy" in names


@pytest.fixture(scope="module")
def convert_markdown():
    from mkapi.page import URIS, convert_markdown
    from mkapi.renderer import load_templates

    load_templates()

    anchors = {"object": "O", "source": "S"}
    uri = "a/b.md"
    namespaces = ("object", "source")
    URIS["object"] = {}
    URIS["source"] = {}

    def covert(markdown: str, kind: TemplateKind):
        def predicate(parser, kind_) -> bool:
            return kind_ == kind

        return convert_markdown(markdown, uri, namespaces, anchors, predicate)

    return covert


def test_convert_markdown_module(convert_markdown):
    m = "# ::: mkapi.doc"
    m = convert_markdown(m, TemplateKind.HEADING)
    assert isinstance(m, str)
    assert m.startswith('<h1 class="mkapi-heading" id="mkapi.doc" markdown="1">')


def test_generate_module_markdown_failure():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("invalid")
    assert m.startswith("!!! failure\n\n    module 'invalid' not found.\n")
    assert not names


def test_link():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["N"] = {"b.c": "y/B.md"}

    m = LINK_PATTERN.match("[A][__mkapi__.__a__.b.c]")
    assert m
    m = _link(m, "x/a.md", "N", {"N": "nn", "source": "S"})
    assert m == ""

    m = LINK_PATTERN.match("[A][__mkapi__.__N__.b.c]")
    assert m
    m = _link(m, "y/a.md", "N", {"N": "nn", "source": "S"})
    assert m == '[[nn]](B.md#b.c "b.c")'


def test_link_not_from_mkapi():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["N"] = {"x.y": "z/a/c.md"}
    m = LINK_PATTERN.match("[A][x.y]")
    assert m
    m = _link(m, "y/a.md", "N", {"N": "nn", "source": "S"})
    assert m == '[A](../z/a/c.md#x.y "x.y")'


def test_link_not_from_mkapi_invalid():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["N"] = {}
    m = LINK_PATTERN.match("[A][x.y]")
    assert m
    m = _link(m, "y/a.md", "N", {"N": "nn", "source": "S"})
    assert m == "[A][x.y]"


def test_link_backticks():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["N"] = {"x.y": "p/B.md"}
    m = LINK_PATTERN.match("[`A`][x.y]")
    assert m
    m = _link(m, "q/r/a.md", "N", {"N": "nn", "source": "S"})
    assert m == '[`A`](../../p/B.md#x.y "x.y")'


def test_link_without_fullname():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["N"] = {"x.y": "q/r/a.md"}
    m = LINK_PATTERN.match("[x.y][]")
    assert m
    m = _link(m, "q/r/a.md", "N", {"N": "nn", "source": "S"})
    assert m == '[x.y](a.md#x.y "x.y")'


def test_link_without_fullname_backticks():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["N"] = {"x.y": "q/s/a.md"}
    m = LINK_PATTERN.match("[`x.y`][]")
    assert m
    m = _link(m, "q/r/a.md", "N", {"N": "nn", "source": "S"})
    assert m == '[`x.y`](../s/a.md#x.y "x.y")'


def test_page_convert_object_page():
    from mkapi.page import URIS, Page
    from mkapi.renderer import load_templates

    load_templates()

    URIS.clear()
    p = Page.create_object("a/b.md", "mkapi.page")
    assert p
    p.generate_markdown()

    assert p.markdown.startswith("# ::: mkapi.page\n")
    assert "## ::: Page mkapi.page\n" in p.markdown
    assert "### ::: Page.generate_markdown mkapi.page\n" in p.markdown
    assert "mkapi.page" in URIS["object"]
    assert URIS["object"]["mkapi.page.Page"] == "a/b.md"

    m = p.convert_markdown("", {"source": "S", "object": "O"})
    assert "mkapi.page.Page.is_documentation_page" in m


def test_page_convert_source_page():
    from mkapi.page import URIS, Page
    from mkapi.renderer import load_templates

    load_templates()

    URIS.clear()
    p = Page.create_source("a/b.md", "mkapi.page")
    assert p
    p.generate_markdown()
    m = p.convert_markdown("", {"source": "S", "object": "O"})
    assert '.[page](b.md#mkapi.page "mkapi.page")</h1>' in m
    assert "class Page:## __mkapi__.mkapi.page.Page" in m
