from pathlib import Path

import markdown
import pytest

import mkapi.renderers
from mkapi.pages import (
    convert_markdown,
    convert_source,
    create_object_markdown,
    create_source_markdown,
    object_paths,
    source_paths,
)
from mkapi.utils import cache_clear


def test_create_object_markdown(tmpdir: Path):
    path = tmpdir / "a.md"
    filters = ["a", "b"]
    names = []

    def predicate(name: str) -> bool:
        names.append(name)
        return True

    name = "mkapi.ast"
    object_paths.clear()
    m = create_object_markdown(name, path, filters, predicate)
    assert not path.exists()
    assert "\n\n## ::: mkapi.ast.Transformer|a|b\n\n" in m
    assert "mkapi.ast" in names
    assert "mkapi.ast.unparse" in names
    assert "mkapi.ast.Transformer.visit_Name" in names
    assert object_paths["mkapi.ast.unparse"] == path
    assert "mkapi.ast.Transformer.visit_Name" in object_paths


def test_create_object_markdown_predicate(tmpdir: Path):
    path = tmpdir / "a.md"

    def predicate(name: str) -> bool:
        if "unparse" in name:
            return False
        return True

    name = "mkapi.ast"

    object_paths.clear()
    m = create_object_markdown(name, path, [], predicate)
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" not in m
    assert "mkapi.ast.Transformer.unparse" not in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m

    object_paths.clear()
    m = create_object_markdown(name, path, [])
    assert not path.exists()
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" in m
    assert "mkapi.ast.Transformer.unparse" in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m


def test_create_object_markdown_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_object_markdown("a.b.c", path, [])
    assert not path.exists()
    assert "!!! failure" in m


def test_create_source_markdown(tmpdir: Path):
    path = tmpdir / "a.md"
    source_paths.clear()
    m = create_source_markdown("mkapi.items", path, [])
    assert not path.exists()
    assert len(m.splitlines()) == 1
    assert "# ::: mkapi.items|source|__mkapi__:mkapi.items=0|" in m
    assert "|__mkapi__:mkapi.items.Element=" in m

    def predicate(name: str) -> bool:
        if "Element" in name:
            return False
        return True

    source_paths.clear()
    m = create_source_markdown("mkapi.items", path, ["x"], predicate)
    assert "# ::: mkapi.items|x|source|__mkapi__:mkapi.items=0|" in m
    assert "|__mkapi__:mkapi.items.Element=" not in m
    assert "mkapi.items" in source_paths
    assert "mkapi.items.Element" not in source_paths


def test_create_source_markdown_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_source_markdown("a.b.c", path, [])
    assert "!!! failure" in m


@pytest.fixture()
def prepare(tmpdir: Path):
    api = Path(tmpdir) / "api/a.md"
    src = Path(tmpdir) / "src/b.md"
    page = Path(tmpdir) / "page/c/d.md"
    name = "mkapi.objects"
    object_paths.clear()
    source_paths.clear()
    obj = create_object_markdown(name, api, [])
    src = create_source_markdown(name, src, [])
    return page, obj, src


@pytest.fixture()
def page(prepare):
    return prepare[0]


@pytest.fixture()
def src(prepare):
    return prepare[2]


mkapi.renderers.load_templates()


def test_convert_markdown_object(page):
    source = "## ::: mkapi.objects.Object\n"
    m = convert_markdown(source, page, object_paths, "A")
    assert 'title="mkapi">mkapi</span>' in m
    assert '[objects](../../api/a.md#mkapi.objects "mkapi.objects").' in m
    assert '<span class="mkapi-source-link">[[A]](../../src/b.md#' in m
    assert 'b.md#mkapi.objects.Object "mkapi.objects.Object")</span>' in m

    source = "## ::: mkapi.objects.create_module\n"
    m = convert_markdown(source, page, object_paths, "A")
    assert '→ </span><span class="mkapi-return">[Module](../../api/a.md#mkapi.' in m
    assert 'a.md#mkapi.objects.Module "mkapi.objects.Module")' in m


def test_convert_markdown_object_failure(page):
    source = "## ::: mkapi.objects.Object_x\n"
    m = convert_markdown(source, page, object_paths, "")
    assert m == "!!! failure\n\n    'mkapi.objects.Object_x' not found.\n"


def test_convert_markdown_link(page):
    source = "[X][mkapi.objects.Object]"
    m = convert_markdown(source, page, object_paths, "A")
    assert m == '[X](../../api/a.md#mkapi.objects.Object "mkapi.objects.Object")'
    source = "[X][mkapi.objects.Object_x]"
    assert convert_markdown(source, page, object_paths, "A") == source


@pytest.mark.parametrize("x", ["[mkapi.objects.Object]", "`[X][mkapi.objects.Object]`"])
def test_convert_markdown_nolink(x, page):
    assert convert_markdown(x, page, object_paths, "A") == x


def test_convert_markdown_source(page):
    source = "[X][mkapi.objects.Object|source]"
    m = convert_markdown(source, page, object_paths, "A")
    assert m == '[X](../../src/b.md#mkapi.objects.Object "mkapi.objects.Object")'
    source = "[X][mkapi.objects.Object_x|source]"
    m = convert_markdown(source, page, object_paths, "A")
    assert m == "[X][mkapi.objects.Object_x|source]"


# def test_convert_source(src):
#     cache_clear()
#     with Path(src).open() as f:
#         m = f.read()
#         m = convert_markdown(m, src, "")
#     assert "## __mkapi__.mkapi.objects.LINK_PATTERN\nLINK_PATTERN = re" in m

#     es = ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]
#     h = markdown.markdown(m, extensions=es)
#     assert '<span class="c1">## __mkapi__.mkapi.objects.is_empty</span>' in h
#     h = convert_source(h, Path(src), "XXX")
#     assert '<span id="mkapi.objects.is_empty" class="mkapi-docs-link">' in h
#     assert '<a href="../../api/a/#mkapi.objects.is_empty">[XXX]</a></span>' in h


# altair.expr is empty
