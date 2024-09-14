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

    parser = Parser.create("examples._styles.google")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set, 1)
    assert '<h1 class="mkapi-heading" id="examples._styles.google" markdown="1">' in m
    assert ">examples.\\_styles.google</h1>" in m


def test_render_heading_export():
    from mkapi.renderer import render_heading

    parser = Parser.create("jinja2.Template")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set, 1)
    assert '<h1 class="mkapi-heading" id="jinja2.Template" markdown="1">' in m


def test_render_heading_alias():
    from mkapi.renderer import render_heading

    parser = Parser.create("examples._styles.ExampleClassGoogle")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set, 1)
    assert 'id="examples._styles.ExampleClassGoogle"' in m
    assert ">examples.\\_styles.ExampleClassGoogle</h1>" in m


def test_render_object_module():
    from mkapi.renderer import render_object

    parser = Parser.create("examples._styles")
    assert parser
    name_set = parser.parse_name_set()
    m = render_object(name_set, 1, "object", [], ["A", "B"])
    assert '<p class="mkapi-object" id="examples._styles" markdown="1">' in m
    x = 'class="mkapi-object-link">[object][__mkapi__.__object__.examples._styles]'
    assert x in m
    assert '<span class="mkapi-object-base">A</span>' in m
    assert '<span class="mkapi-object-base">B</span>' in m


def test_render_object_object():
    from mkapi.renderer import render_object

    parser = Parser.create("mkapi.node.Node")
    assert parser
    name_set = parser.parse_name_set()
    m = render_object(name_set, 1, "source", [], [])
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

    m = render("mkapi.ast", None, level, "object", predicate)
    assert f'<h{level} class="mkapi-heading" id="mkapi.ast" markdown="1">' in m

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
    from mkapi.node import iter_module_members
    from mkapi.object import Module, get_object
    from mkapi.renderer import _get_source

    obj = get_object("mkapi.object")
    assert isinstance(obj, Module)
    s = _get_source(obj)

    for name, _ in iter_module_members("mkapi.object"):
        assert s.count(f"## __mkapi__.mkapi.object.{name}\n") == 1
