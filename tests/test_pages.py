from pathlib import Path

import markdown
import pytest

import mkapi.renderers
from mkapi.pages import (
    convert_markdown,
    convert_source,
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
    m = create_markdown(name, path, filters, predicate)
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
    m = create_markdown(name, path, [], predicate)
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" not in m
    assert "mkapi.ast.Transformer.unparse" not in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m

    object_paths.clear()
    m = create_markdown(name, path, [])
    assert not path.exists()
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" in m
    assert "mkapi.ast.Transformer.unparse" in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m


def test_create_object_markdown_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_markdown("a.b.c", path, [])
    assert not path.exists()
    assert "!!! failure" in m


def test_create_source_markdown(tmpdir: Path):
    path = tmpdir / "a.md"
    source_paths.clear()
    m = create_markdown("mkapi.items", path, [], is_source=True)
    assert not path.exists()
    assert "# ::: mkapi.items|__mkapi__:mkapi.items=0\n" in m
    assert "## ::: mkapi.items.Element|__mkapi__:mkapi.items.Element=" in m

    def predicate(name: str) -> bool:
        if "Element" in name:
            return False
        return True

    source_paths.clear()
    m = create_markdown("mkapi.items", path, ["x"], predicate, is_source=True)
    assert "# ::: mkapi.items|x|__mkapi__:mkapi.items=0\n" in m
    assert "__mkapi__:mkapi.items.Element=" not in m
    assert "mkapi.items" in source_paths
    assert "mkapi.items.Element" not in source_paths


def test_create_source_markdown_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_markdown("a.b.c", path, [], is_source=True)
    assert "!!! failure" in m


@pytest.fixture()
def prepare(tmpdir: Path):
    api = Path(tmpdir) / "api/a.md"
    src = Path(tmpdir) / "src/b.md"
    page = Path(tmpdir) / "page/c/d.md"
    name = "mkapi.objects"
    object_paths.clear()
    source_paths.clear()
    obj = create_markdown(name, api, [], is_source=False)
    src = create_markdown(name, src, [], is_source=True)
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
    m = convert_markdown(source, page, "A")
    assert 'title="mkapi">mkapi</span>' in m
    assert '[objects](../../api/a.md#mkapi.objects "mkapi.objects").' in m
    assert '<span class="mkapi-source-link">[[A]](../../src/b.md#' in m
    assert 'b.md#mkapi.objects.Object "mkapi.objects.Object")</span>' in m

    source = "## ::: mkapi.objects.create_module\n"
    m = convert_markdown(source, page, "A")
    assert '→ </span><span class="mkapi-return">[Module](../../api/a.md#mkapi.' in m
    assert 'a.md#mkapi.objects.Module "mkapi.objects.Module")' in m


def test_convert_markdown_object_failure(page):
    source = "## ::: mkapi.objects.Object_x\n"
    m = convert_markdown(source, page, "")
    assert m == "!!! failure\n\n    'mkapi.objects.Object_x' not found.\n"


def test_convert_markdown_link(page):
    source = "[X][mkapi.objects.Object]"
    m = convert_markdown(source, page, "A")
    assert m == '[X](../../api/a.md#mkapi.objects.Object "mkapi.objects.Object")'
    source = "[X][mkapi.objects.Object_x]"
    assert convert_markdown(source, page, "A") == source


@pytest.mark.parametrize("x", ["[mkapi.objects.Object]", "`[X][mkapi.objects.Object]`"])
def test_convert_markdown_nolink(x, page):
    assert convert_markdown(x, page, "A") == x


def test_convert_source(src, page):
    cache_clear()
    m = convert_markdown(src, page, "A", is_source=True)
    assert '<h1 id="mkapi.objects" class="mkapi-heading" markdown="1">' in m
    assert '<span class="mkapi-docs-link">[[A]](../../api/a.md#mkapi.objects' in m
    assert "``` {.python .mkapi-source}" in m
    assert "class Attribute(Member):## __mkapi__.mkapi.objects.Attribute" in m
