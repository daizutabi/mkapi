import pytest

from mkapi.renderer import TemplateKind


def test_generate_module_markdown():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("mkapi.doc")
    assert m.startswith("# ::: mkapi.doc\n")
    assert "\n## ::: mkapi.doc.Item\n" in m
    assert "\n### ::: mkapi.doc.Item.clone\n" in m
    assert "\n## ::: mkapi.doc.merge\n" in m

    assert "mkapi.doc" in names
    assert "mkapi.doc.Item" in names
    assert "mkapi.doc.Item.clone" in names
    assert "mkapi.doc.merge" in names


def test_generate_module_markdown_export():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("jinja2")
    assert m.startswith("# ::: jinja2\n")
    assert "\n## ::: jinja2.Template\n" in m
    assert "\n### ::: jinja2.Template.render\n" in m


def test_generate_module_markdown_alias():
    from mkapi.page import generate_module_markdown

    m, names = generate_module_markdown("examples.styles")
    assert m.startswith("# ::: examples.styles\n")
    assert "\n## ::: examples.styles.ExampleClassGoogle\n" in m
    assert "\n## ::: examples.styles.ExampleClassNumPy\n" in m

    assert "examples.styles" in names
    assert "examples.styles.ExampleClassGoogle" in names
    assert "examples.styles.ExampleClassNumPy" in names


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

    # markdown = convert_markdown("## ::: mkapi.ast.Transformer", "/root/a/b/c.md")
    # assert markdown.startswith("## ::: mkapi.ast.Transformer")


# from pathlib import Path

# import markdown

# import mkapi.renderer
# from mkapi.page import (
#     convert_html,
#     convert_markdown,
#     create_markdown,
# )
# from mkapi.utils import cache_clear

# mkapi.renderer.load_templates()


# def test_create_markdown_markdown():
#     filters = ["a", "b"]
#     names_predicate = []

#     def predicate(name: str) -> bool:
#         names_predicate.append(name)
#         return True

#     name = "mkapi.ast"
#     m, names = create_markdown(name, filters, predicate)
#     assert "\n\n## ::: mkapi.ast.Transformer|a|b\n\n" in m
#     for ns in [names, names_predicate]:
#         assert "mkapi.ast" in ns
#         assert "mkapi.ast.unparse" in ns
#         assert "mkapi.ast.Transformer.visit_Name" in ns


# def test_create_object_markdown_predicate():
#     def predicate(name: str) -> bool:
#         if "unparse" in name:
#             return False
#         return True

#     name = "mkapi.ast"

#     m, names = create_markdown(name, [], predicate)
#     for ns in [m, names]:
#         assert "mkapi.ast.is_function" in ns
#         assert "mkapi.ast.unparse" not in ns
#         assert "mkapi.ast.Transformer.unparse" not in ns
#         assert "mkapi.ast.StringTransformer.visit_Constant" in ns

#     m, names = create_markdown(name, [])
#     for ns in [m, names]:
#         assert "mkapi.ast.is_function" in ns
#         assert "mkapi.ast.unparse" in ns
#         assert "mkapi.ast.Transformer.unparse" in ns
#         assert "mkapi.ast.StringTransformer.visit_Constant" in ns


# def test_create_markdown_failure():
#     m, names = create_markdown("a.b.c", [])
#     assert "!!! failure" in m
#     assert not names


# def test_convert_markdown():
#     source = "## ::: mkapi.objects.Object\n"
#     path = Path("/root/a/b/c.md")
#     paths = {}
#     paths["object"] = {"mkapi.object.Object": Path("/root/api/x.md")}
#     paths["source"] = {"mkapi.object.Object": Path("/root/src/x.md")}
#     namespaces = ("object", "source")
#     anchors = {"object": "docs", "source": "source"}
#     m = convert_markdown(source, path, namespaces, paths, anchors)
#     assert '<span class="mkapi-tooltip" title="mkapi">' in m
#     assert '</span>.[Object](../../api/x.md#mkapi.objects.Object "mkapi.object.Object")' in m
#     assert 'link">[[source]](../../src/x.md#mkapi.objects.Object "mkapi.object.Object")' in m
#     namespaces = ("source", "object")
#     m = convert_markdown(source, path, namespaces, paths, anchors)
#     assert '</span>.[Object](../../src/x.md#mkapi.objects.Object "mkapi.object.Object")' in m
#     assert 'link">[[docs]](../../api/x.md#mkapi.objects.Object "mkapi.object.Object")' in m


# def test_convert_html():
#     cache_clear()
#     source = "## ::: mkapi.objects.Object\n"
#     path = Path("/root/a/b/c.md")
#     paths = {}
#     paths["object"] = {"mkapi.object.Object": Path("/root/api/x.md")}
#     paths["source"] = {"mkapi.object.Object": Path("/root/src/x.md")}
#     paths["object"]["mkapi.object.Object.__repr__"] = Path("/root/X/x.md")
#     namespaces = ("object", "source")
#     anchors = {"object": "docs", "source": "source"}
#     m = convert_markdown(source, path, namespaces, paths, anchors)

#     es = ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]
#     h = markdown.markdown(m, extensions=es)
#     h = convert_html(h, path, paths["object"], anchors["object"])
#     assert '<a href="../../../X/x/#mkapi.objects.Object.__repr__">[docs]</a>' in h


# def test_create_markdown_alias():
#     m = create_markdown("examples.styles", [])
#     assert "# ::: examples.styles\n\n" in m[0]
#     assert "## ::: examples.styles.ExampleClassGoogle\n\n" in m[0]
#     assert "## ::: examples.styles.ExampleClassNumPy\n" in m[0]
#     assert "examples.styles" in m[1]
#     assert "examples.styles.ExampleClassGoogle" in m[1]
#     assert "examples.styles.ExampleClassNumPy" in m[1]
