import pytest

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

    parser = Parser.create("examples.styles.google")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set.node.id, name_set.node.fullname, 1)
    assert '<h1 class="mkapi-heading" id="examples.styles.google" markdown="1">' in m
    assert "[examples][__mkapi__.examples].[styles][__mkapi__.examples.styles]" in m


def test_render_heading_export():
    from mkapi.renderer import render_heading

    parser = Parser.create("jinja2.Template")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set.node.id, name_set.node.fullname, 1)
    assert '<h1 class="mkapi-heading" id="jinja2.Template" markdown="1">' in m


def test_render_heading_alias():
    from mkapi.renderer import render_heading

    parser = Parser.create("examples.styles.ExampleClassGoogle")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set.node.id, name_set.node.fullname, 1)
    assert 'id="examples.styles.ExampleClassGoogle"' in m
    assert "[ExampleClassGoogle][__mkapi__.examples.styles.ExampleClassGoogle]" in m


def test_render_object_module():
    from mkapi.renderer import render_object

    parser = Parser.create("examples.styles")
    assert parser
    name_set = parser.parse_name_set()
    m = render_object(parser.obj, name_set, "object", [], ["A", "B"])
    assert '<p class="mkapi-object" id="examples.styles" markdown="1">' in m
    x = 'class="mkapi-object-link">[object][__mkapi__.__object__.examples.styles]'
    assert x in m
    assert '<span class="mkapi-object-base">A</span>' in m
    assert '<span class="mkapi-object-base">B</span>' in m


def test_render_object_object():
    from mkapi.renderer import render_object

    parser = Parser.create("mkapi.node.Node")
    assert parser
    name_set = parser.parse_name_set()
    m = render_object(parser.obj, name_set, "source", [], [])
    print(m)
    x = 'class="mkapi-object-link">[source][__mkapi__.__source__.mkapi'
    assert x in m
    assert "[Node][__mkapi__.mkapi.node.Node]" in m


def test_render_source_module():
    from mkapi.renderer import render_source

    parser = Parser.create("mkapi.ast")
    assert parser
    m = render_source(parser.obj)
    assert m.startswith("``` {.python .mkapi-source}\n")
    assert "Iterator[AST]:## __mkapi__.mkapi.ast.iter_child_nodes" in m
    assert "def _iter_assign_nodes(## __mkapi__.mkapi.ast._iter_assign_nodes" in m


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

    m = render("mkapi.ast", level, "object", predicate)
    assert f'<h{level} class="mkapi-heading" id="mkapi.ast" markdown="1">' in m

    if source:
        assert "```" in m
    else:
        assert "```" not in m

    assert '<div class="mkapi-document" markdown="1">' in m


def test_render_module_invalid():
    from mkapi.renderer import render

    m = render("mkapi.invalid", 1, "object", None)
    assert "!!! failure" in m
    assert "'mkapi.invalid' not found." in m
