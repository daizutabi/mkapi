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

    m, names = generate_module_markdown("astdoc.doc")
    assert m.startswith("# ::: astdoc.doc\n")
    assert "\n## ::: Item astdoc.doc\n" in m
    assert "\n### ::: Item.clone astdoc.doc\n" in m
    assert "\n## ::: merge astdoc.doc\n" in m

    assert "astdoc.doc" in names
    assert "astdoc.doc.Item" in names
    assert "astdoc.doc.Item.clone" in names
    assert "astdoc.doc.merge" in names


def test_generate_module_markdown_export():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("jinja2")
    assert m.startswith("# ::: jinja2\n")
    assert "\n## ::: Template jinja2\n" in m
    assert "\n### ::: Template.render jinja2\n" in m


def test_generate_module_markdown_alias():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("examples")
    assert m.startswith("# ::: examples\n")
    assert "\n## ::: ExampleClassA examples\n" in m
    assert "\n## ::: ExampleClassB examples" in m

    assert "examples" in names
    assert "examples.ExampleClassA" in names
    assert "examples.ExampleClassB" in names


@pytest.fixture(scope="module")
def convert_markdown():
    from mkapi.page import URIS, convert_markdown
    from mkapi.renderer import load_templates

    load_templates()

    uri = "a/b.md"
    namespaces = ("object", "source")
    URIS["object"] = {}
    URIS["source"] = {}

    def covert(markdown: str, kind: TemplateKind):
        def predicate(parser, kind_) -> bool:
            return kind_ == kind

        return convert_markdown(markdown, uri, namespaces, predicate)

    return covert


def test_convert_markdown_module(convert_markdown):
    m = "# ::: mkapi.page"
    m = convert_markdown(m, TemplateKind.HEADING)
    assert isinstance(m, str)
    assert m.startswith('<h1 class="mkapi-heading" id="mkapi.page" markdown="1">')


def test_generate_module_markdown_failure():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("invalid")
    assert m.startswith("!!! failure\n\n    module 'invalid' not found.\n")
    assert not names


def test_generate_object_markdown():
    from mkapi.page import generate_object_markdown

    m, names = generate_object_markdown("Item", "astdoc.doc")
    assert m.startswith("# ::: Item astdoc.doc\n")
    assert "\n## ::: Item.clone astdoc.doc" in m
    assert "merge astdoc.doc" not in m

    assert "astdoc.doc" not in names
    assert "astdoc.doc.Item" in names
    assert "astdoc.doc.Item.clone" in names
    assert "astdoc.doc.merge" not in names


def test_generate_object_markdown_failure_module():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("invalid.Item")
    assert m.startswith("!!! failure\n\n    module 'invalid' not found.\n")
    assert not names


def test_generate_object_markdown_failure_object():
    from mkapi.page import generate_object_markdown

    m, names = generate_object_markdown("Invalid", "astdoc.doc")
    x = "!!! failure\n\n    object 'Invalid' not found in module 'astdoc.doc'.\n"
    assert m.startswith(x)
    assert not names


def test_link():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["source"] = {"b.c": "y/B.md"}

    m = LINK_PATTERN.match("[A][__mkapi__.__a__.b.c]")
    assert m
    m = _link(m, "x/a.md", "N")
    assert m == ""

    m = LINK_PATTERN.match("[A][__mkapi__.__source__.b.c]")
    assert m
    m = _link(m, "y/a.md", "N")
    assert m == '[mkapi_source_mkapi](B.md#b.c "Go to source")'


def test_link_not_from_mkapi():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["definition"] = {"x.y": "z/a/c.md"}
    m = LINK_PATTERN.match("[A][x.y]")
    assert m
    m = _link(m, "y/a.md", "definition")
    assert m == '[A](../z/a/c.md#x.y "x.y")'


def test_link_not_from_mkapi_invalid():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["object"] = {}
    m = LINK_PATTERN.match("[A][x.y]")
    assert m
    m = _link(m, "y/a.md", "object")
    assert m == "[A][x.y]"


def test_link_backticks():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["source"] = {"x.y": "p/B.md"}
    m = LINK_PATTERN.match("[`A`][x.y]")
    assert m
    m = _link(m, "q/r/a.md", "source")
    assert m == '[`A`](../../p/B.md#x.y "x.y")'


def test_link_without_fullname():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["object"] = {"x.y": "q/r/a.md"}
    m = LINK_PATTERN.match("[x.y][]")
    assert m
    m = _link(m, "q/r/a.md", "object")
    assert m == '[x.y](a.md#x.y "x.y")'


def test_link_without_fullname_backticks():
    from mkapi.page import LINK_PATTERN, URIS, _link

    URIS["source"] = {"x.y": "q/s/a.md"}
    m = LINK_PATTERN.match("[`x.y`][]")
    assert m
    m = _link(m, "q/r/a.md", "source")
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

    m = p.convert_markdown("")
    assert "mkapi.page.Page.is_documentation_page" in m


def test_page_convert_source_page():
    from mkapi.page import URIS, Page
    from mkapi.renderer import load_templates

    load_templates()

    URIS.clear()
    p = Page.create_source("a/b.md", "mkapi.page")
    assert p
    p.generate_markdown()
    m = p.convert_markdown("")
    assert "class Page:## __mkapi__.mkapi.page.Page" in m
