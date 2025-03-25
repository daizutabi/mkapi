import pytest
from astdoc.node import iter_module_members
from astdoc.object import Module, get_object

from mkapi.parser import Parser
from mkapi.renderer import TemplateKind


@pytest.fixture(autouse=True)
def _load_templates():
    from mkapi.renderer import load_templates

    load_templates()


def test_load_templates():
    from mkapi.renderer import templates

    assert "heading" in templates
    assert "object" in templates
    assert "document" in templates
    assert "source" in templates


def test_render_heading_module():
    from mkapi.renderer import render_heading

    parser = Parser.create("examples.a")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set, 1)
    assert '<h1 class="mkapi-heading" id="examples.a" markdown="1">' in m
    assert ">examples.a</h1>" in m


def test_render_heading_export():
    from mkapi.renderer import render_heading

    parser = Parser.create("jinja2.Template")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set, 1)
    assert '<h1 class="mkapi-heading" id="jinja2.Template" markdown="1">' in m


def test_render_heading_alias():
    from mkapi.renderer import render_heading

    parser = Parser.create("examples.ExampleClassA")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set, 1)
    assert 'id="examples.ExampleClassA"' in m
    assert ">examples.ExampleClassA</h1>" in m


def test_render_object_module():
    from mkapi.renderer import render_object

    parser = Parser.create("examples")
    assert parser
    name_set = parser.parse_name_set()
    m = render_object(name_set, 1, "object", [])
    x = '<p class="mkapi-object mkapi-page-object" id="examples" markdown="1">'
    assert x in m
    x = "[object][__mkapi__.__object__.examples]"
    assert x in m


def test_render_object_object():
    from mkapi.renderer import render_object

    parser = Parser.create("mkapi.page.Page")
    assert parser
    name_set = parser.parse_name_set()
    m = render_object(name_set, 1, "source", [])
    x = "[source][__mkapi__.__source__.mkapi"
    assert x in m
    assert "[Page][__mkapi__.mkapi.page.Page]" in m


def test_render_source_module():
    from mkapi.renderer import render_source

    parser = Parser.create("astdoc.ast")
    assert parser
    m = render_source(parser.obj)
    assert m.startswith('``` {.python .mkapi-source .no-copy linenums="1"}\n')
    assert "Iterator[AST]:## __mkapi__.astdoc.ast.iter_child_nodes" in m
    assert "def _iter_assign_nodes(## __mkapi__.astdoc.ast._iter_assign_nodes" in m


def test_render_source_invalid():
    from mkapi.renderer import render_source

    assert render_source(None) == ""  # type: ignore


@pytest.mark.parametrize("level", [1, 2])
@pytest.mark.parametrize("source", [True, False])
def test_render_module(level: int, source: bool):
    from mkapi.renderer import render

    def predicate(parser: Parser, kind: TemplateKind):
        if source:
            return True

        return kind != TemplateKind.SOURCE

    m = render("mkapi.nav", None, level, "object", predicate)
    assert f'<h{level} class="mkapi-heading" id="mkapi.nav" markdown="1">' in m

    if source:
        assert "```" in m
    else:
        assert "```" not in m

    assert '<div class="mkapi-document" markdown="1">' in m


def test_render_module_invalid():
    from mkapi.renderer import render

    m = render("mkapi.invalid", None, 1, "object", None)
    assert "!!! failure" in m
    assert "'mkapi.invalid' not found." in m


def test_get_source_id_must_be_unique():
    from mkapi.renderer import _get_source

    obj = get_object("mkapi.plugin")
    assert isinstance(obj, Module)
    s = _get_source(obj)

    for name, _ in iter_module_members("mkapi.plugin"):
        assert s.count(f"## __mkapi__.mkapi.plugin.{name}\n") == 1


@pytest.mark.parametrize(
    ("source", "expected"),
    [("a```b``c", 3), ("abc", 0)],
)
def test_find_max_backticks(source: str, expected: int):
    from mkapi.renderer import find_max_backticks

    assert find_max_backticks(source) == expected
