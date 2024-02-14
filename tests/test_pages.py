from pathlib import Path

import markdown
import pytest

import mkapi.renderers
from mkapi.pages import (
    PageKind,
    convert_html,
    convert_markdown,
    create_markdown,
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
    m = create_markdown(name, path, PageKind.OBJECT, filters, predicate)
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
    m = create_markdown(name, path, PageKind.OBJECT, [], predicate)
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" not in m
    assert "mkapi.ast.Transformer.unparse" not in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m

    object_paths.clear()
    m = create_markdown(name, path, PageKind.OBJECT, [])
    assert not path.exists()
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" in m
    assert "mkapi.ast.Transformer.unparse" in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m


def test_create_object_markdown_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_markdown("a.b.c", path, PageKind.OBJECT, [])
    assert not path.exists()
    assert "!!! failure" in m


def test_create_source_markdown(tmpdir: Path):
    path = tmpdir / "a.md"
    source_paths.clear()
    m = create_markdown("mkapi.items", path, PageKind.SOURCE, [])
    assert not path.exists()
    assert "# ::: mkapi.items|__mkapi__:mkapi.items=0\n" in m
    assert "## ::: mkapi.items.Item|__mkapi__:mkapi.items.Item=" in m

    def predicate(name: str) -> bool:
        if "Item" in name:
            return False
        return True

    source_paths.clear()
    m = create_markdown("mkapi.items", path, PageKind.SOURCE, ["x"], predicate)
    assert "# ::: mkapi.items|x|__mkapi__:mkapi.items=0\n" in m
    assert "__mkapi__:mkapi.items.Item=" not in m
    assert "mkapi.items" in source_paths
    assert "mkapi.items.Item" not in source_paths


def test_create_source_markdown_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_markdown("a.b.c", path, PageKind.SOURCE, [])
    assert "!!! failure" in m


@pytest.fixture
def prepare(tmpdir: Path):
    api = Path(tmpdir) / "api/a.md"
    src = Path(tmpdir) / "src/b.md"
    page = Path(tmpdir) / "page/c/d.md"
    name = "mkapi.objects"
    object_paths.clear()
    source_paths.clear()
    obj = create_markdown(name, api, PageKind.OBJECT, [])
    src = create_markdown(name, src, PageKind.SOURCE, [])
    return page, obj, src


@pytest.fixture
def page(prepare):
    return prepare[0]


@pytest.fixture
def src(prepare):
    return prepare[2]


mkapi.renderers.load_templates()


def test_convert_markdown_object(page):
    source = "## ::: mkapi.objects.Object\n"
    m = convert_markdown(source, page, PageKind.OBJECT, "A")
    assert 'title="mkapi">mkapi</span>' in m
    assert '[objects](../../api/a.md#mkapi.objects "mkapi.objects").' in m
    assert '<span class="mkapi-source-link">[[A]](../../src/b.md#' in m
    assert 'b.md#mkapi.objects.Object "mkapi.objects.Object")</span>' in m

    source = "## ::: mkapi.objects.create_module\n"
    m = convert_markdown(source, page, PageKind.OBJECT, "A")
    assert '→ </span><span class="mkapi-return">[Module](../../api/a.md#mkapi.' in m
    assert 'a.md#mkapi.objects.Module "mkapi.objects.Module")' in m


def test_convert_markdown_object_failure(page):
    source = "## ::: mkapi.objects.Object_x\n"
    m = convert_markdown(source, page, PageKind.OBJECT, "")
    assert m == "!!! failure\n\n    'mkapi.objects.Object_x' not found.\n"


def test_convert_markdown_link(page):
    source = "[X][mkapi.objects.Object]"
    m = convert_markdown(source, page, PageKind.OBJECT, "A")
    assert m == '[X](../../api/a.md#mkapi.objects.Object "mkapi.objects.Object")'
    source = "[X][mkapi.objects.Object_x]"
    assert convert_markdown(source, page, PageKind.OBJECT, "A") == source


@pytest.mark.parametrize("x", ["[mkapi.objects.Object]", "`[X][mkapi.objects.Object]`"])
def test_convert_markdown_nolink(x, page):
    assert convert_markdown(x, page, PageKind.OBJECT, "A") == x


def test_convert_html(src, page):
    cache_clear()
    m = convert_markdown(src, page, PageKind.SOURCE, "A")
    assert '<h1 class="mkapi-header" id="mkapi.objects" markdown="1">' in m
    assert '<span class="mkapi-docs-link">[[A]](../../api/a.md#mkapi.objects' in m
    assert "``` {.python .mkapi-source}" in m
    assert "class Attribute(Member):## __mkapi__.mkapi.objects.Attribute" in m

    es = ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]
    h = markdown.markdown(m, extensions=es)
    assert '<h2 class="mkapi-heading" id="mkapi.objects.Object">' in h

    h = convert_html(h, page, "AAA")
    assert "mkapi-dummy-heading" not in h
    assert '<a href="../../../api/a/#mkapi.objects.is_empty">[AAA]</a></span>' in h
