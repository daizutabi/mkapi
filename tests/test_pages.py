from pathlib import Path

import markdown

import mkapi.renderers
from mkapi.pages import (
    convert_html,
    convert_markdown,
    create_markdown,
)
from mkapi.utils import cache_clear


def test_create_markdown_markdown():
    filters = ["a", "b"]
    names_p = []

    def predicate(name: str) -> bool:
        names_p.append(name)
        return True

    name = "mkapi.ast"
    m, names = create_markdown(name, filters, predicate)
    assert "\n\n## ::: mkapi.ast.Transformer|a|b\n\n" in m
    for ns in [names, names_p]:
        assert "mkapi.ast" in ns
        assert "mkapi.ast.unparse" in ns
        assert "mkapi.ast.Transformer.visit_Name" in ns


def test_create_object_markdown_predicate():
    def predicate(name: str) -> bool:
        if "unparse" in name:
            return False
        return True

    name = "mkapi.ast"

    m, names = create_markdown(name, [], predicate)
    for ns in [m, names]:
        assert "mkapi.ast.is_function" in ns
        assert "mkapi.ast.unparse" not in ns
        assert "mkapi.ast.Transformer.unparse" not in ns
        assert "mkapi.ast.StringTransformer.visit_Constant" in ns

    m, names = create_markdown(name, [])
    for ns in [m, names]:
        assert "mkapi.ast.is_function" in ns
        assert "mkapi.ast.unparse" in ns
        assert "mkapi.ast.Transformer.unparse" in ns
        assert "mkapi.ast.StringTransformer.visit_Constant" in ns


def test_create_markdown_failure():
    m, names = create_markdown("a.b.c", [])
    assert "!!! failure" in m
    assert not names


mkapi.renderers.load_templates()


def test_convert_markdown():
    source = "## ::: mkapi.objects.Object\n"
    path = Path("/root/a/b/c.md")
    paths = {}
    paths["object"] = {"mkapi.objects.Object": Path("/root/api/x.md")}
    paths["source"] = {"mkapi.objects.Object": Path("/root/src/x.md")}
    namespaces = ("object", "source")
    anchors = {"object": "docs", "source": "source"}
    m = convert_markdown(source, path, namespaces, paths, anchors)
    assert '<span class="mkapi-tooltip" title="mkapi">' in m
    assert '</span>.[Object](../../api/x.md#mkapi.objects.Object "mkapi.objects.Object")' in m
    assert 'link">[[source]](../../src/x.md#mkapi.objects.Object "mkapi.objects.Object")' in m
    namespaces = ("source", "object")
    m = convert_markdown(source, path, namespaces, paths, anchors)
    assert '</span>.[Object](../../src/x.md#mkapi.objects.Object "mkapi.objects.Object")' in m
    assert 'link">[[docs]](../../api/x.md#mkapi.objects.Object "mkapi.objects.Object")' in m


def test_convert_html():
    cache_clear()
    source = "## ::: mkapi.objects.Object\n"
    path = Path("/root/a/b/c.md")
    paths = {}
    paths["object"] = {"mkapi.objects.Object": Path("/root/api/x.md")}
    paths["source"] = {"mkapi.objects.Object": Path("/root/src/x.md")}
    paths["object"]["mkapi.objects.Object.__repr__"] = Path("/root/X/x.md")
    namespaces = ("object", "source")
    anchors = {"object": "docs", "source": "source"}
    m = convert_markdown(source, path, namespaces, paths, anchors)

    es = ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]
    h = markdown.markdown(m, extensions=es)
    h = convert_html(h, path, paths["object"], anchors["object"])
    assert '<a href="../../../X/x/#mkapi.objects.Object.__repr__">[docs]</a>' in h


def test_create_markdown_alias():
    m = create_markdown("examples.styles", [])
    assert "# ::: examples.styles\n\n" in m[0]
    assert "## ::: examples.styles.ExampleClassGoogle\n\n" in m[0]
    assert "## ::: examples.styles.ExampleClassNumPy\n" in m[0]
    assert "examples.styles" in m[1]
    assert "examples.styles.ExampleClassGoogle" in m[1]
    assert "examples.styles.ExampleClassNumPy" in m[1]
