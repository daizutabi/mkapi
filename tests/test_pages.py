from pathlib import Path

import markdown
import pytest

import mkapi.renderers
from mkapi.importlib import cache_clear
from mkapi.pages import (
    _split_name_maxdepth,
    convert_markdown,
    convert_source,
    create_object_page,
    create_source_page,
    object_paths,
    source_paths,
)


def test_split_name_maxdepth():
    assert _split_name_maxdepth("name") == ("name", 0)
    assert _split_name_maxdepth("name.*") == ("name", 1)
    assert _split_name_maxdepth("name.**") == ("name", 2)
    assert _split_name_maxdepth("name.") == ("name.", 0)


def test_create_object_page(tmpdir: Path):
    path = tmpdir / "a.md"
    filters = ["a", "b"]
    names = []

    def predicate(name: str) -> bool:
        names.append(name)
        return True

    name = "mkapi.ast"
    object_paths.clear()
    m = create_object_page(name, path, filters, predicate, save=True)
    assert path.exists()
    with path.open() as f:
        assert f.read() == m
    assert object_paths["mkapi.ast"] == path

    assert m == "# ::: mkapi.ast|a|b\n"
    assert names == ["mkapi.ast"]

    names.clear()
    object_paths.clear()
    name = "mkapi.ast.*"
    m = create_object_page(name, path, filters, predicate, save=True)
    assert "\n\n## ::: mkapi.ast.Transformer|a|b\n\n" in m
    assert "mkapi.ast" in names
    assert "mkapi.ast.unparse" in names
    assert "mkapi.ast.Transformer.visit_Name" not in names
    assert object_paths["mkapi.ast.unparse"] == path
    assert "mkapi.ast.Transformer.visit_Name" not in object_paths

    names.clear()
    object_paths.clear()
    name = "mkapi.ast.**"
    m = create_object_page(name, path, filters, predicate, save=True)
    assert "### ::: mkapi.ast.StringTransformer.visit_Constant|a|b" in m
    assert "mkapi.ast.Transformer.visit_Name" in names
    assert "mkapi.ast.Transformer.visit_Name" in object_paths


def test_create_object_page_predicate(tmpdir: Path):
    path = tmpdir / "a.md"

    def predicate(name: str) -> bool:
        if "unparse" in name:
            return False
        return True

    name = "mkapi.ast.**"

    object_paths.clear()
    m = create_object_page(name, path, [], predicate, save=False)
    assert not object_paths
    assert not path.exists()
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" not in m
    assert "mkapi.ast.Transformer.unparse" not in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m

    m = create_object_page(name, path, [], save=True)
    assert path.exists()
    assert "mkapi.ast.is_function" in m
    assert "mkapi.ast.unparse" in m
    assert "mkapi.ast.Transformer.unparse" in m
    assert "mkapi.ast.StringTransformer.visit_Constant" in m


def test_create_object_page_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_object_page("a.b.c", path, [], save=True)
    assert path.exists()
    assert "!!! failure" in m


def test_create_source_page(tmpdir: Path):
    path = tmpdir / "a.md"
    source_paths.clear()
    m = create_source_page("mkapi.items.**", path, [], save=False)
    assert not path.exists()
    assert not source_paths
    assert len(m.splitlines()) == 1
    assert "# ::: mkapi.items|source|__mkapi__:mkapi.items=0|" in m
    assert "|__mkapi__:mkapi.items.Element=" in m

    def predicate(name: str) -> bool:
        if "Element" in name:
            return False
        return True

    source_paths.clear()
    m = create_source_page("mkapi.items.**", path, ["x"], predicate)
    assert path.exists()
    with path.open() as f:
        assert f.read() == m
    assert "# ::: mkapi.items|x|source|__mkapi__:mkapi.items=0|" in m
    assert "|__mkapi__:mkapi.items.Element=" not in m
    assert "mkapi.items" in source_paths
    assert "mkapi.items.Element" not in source_paths


def test_create_source_page_failure(tmpdir: Path):
    path = tmpdir / "a.md"
    m = create_source_page("a.b.c", path, [], save=True)
    assert path.exists()
    assert "!!! failure" in m


@pytest.fixture()
def paths(tmpdir: Path):
    api = Path(tmpdir) / "api/a.md"
    api.parent.mkdir()
    src = Path(tmpdir) / "src/b.md"
    src.parent.mkdir()
    page = Path(tmpdir) / "page/c/d.md"
    page.parent.mkdir(parents=True)
    name = "mkapi.objects.**"
    object_paths.clear()
    source_paths.clear()
    create_object_page(name, api, [], save=True)
    create_source_page(name, src, [], save=True)
    return api, src, page


@pytest.fixture()
def page(paths):
    return paths[2].as_posix()


@pytest.fixture()
def src(paths):
    return paths[1].as_posix()


mkapi.renderers.load_templates()


def test_convert_markdown_object(page):
    source = "## ::: mkapi.objects.Object\n"
    m = convert_markdown(source, page, "A", ["sourcelink"])
    assert 'title="mkapi">mkapi</span>' in m
    assert '[objects](../../api/a.md#mkapi.objects "mkapi.objects").' in m
    assert '<span class="mkapi-source-link">[[A]](../../src/b.md#' in m
    assert 'b.md#mkapi.objects.Object "mkapi.objects.Object")</span>' in m

    source = "## ::: mkapi.objects.create_module\n"
    m = convert_markdown(source, page, "A", [])
    assert "mkapi-source-link" not in m
    assert '→ </span><span class="mkapi-return">[Module](../../api/a.md#mkapi.' in m
    assert 'a.md#mkapi.objects.Module "mkapi.objects.Module")' in m

    source = "## ::: mkapi.objects.create_module|sourcelink\n"
    m = convert_markdown(source, page, "A", [])
    assert "mkapi-source-link" in m


def test_convert_markdown_object_failure(page):
    source = "## ::: mkapi.objects.Object_x\n"
    m = convert_markdown(source, page, "", [])
    assert m == "!!! failure\n\n    'mkapi.objects.Object_x' not found.\n"


def test_convert_markdown_link(page):
    source = "[X][mkapi.objects.Object]"
    m = convert_markdown(source, page, "A", [])
    assert m == '[X](../../api/a.md#mkapi.objects.Object "mkapi.objects.Object")'
    source = "[X][mkapi.objects.Object_x]"
    assert convert_markdown(source, page, "A", []) == source


@pytest.mark.parametrize("x", ["[mkapi.objects.Object]", "`[X][mkapi.objects.Object]`"])
def test_convert_markdown_nolink(x, page):
    assert convert_markdown(x, page, "A", []) == x


def test_convert_markdown_source(page):
    source = "[X][mkapi.objects.Object|source]"
    m = convert_markdown(source, page, "A", [])
    assert m == '[X](../../src/b.md#mkapi.objects.Object "mkapi.objects.Object")'
    source = "[X][mkapi.objects.Object_x|source]"
    assert convert_markdown(source, page, "A", []) == "X"


def test_convert_source(src):
    cache_clear()
    with Path(src).open() as f:
        m = f.read()
        m = convert_markdown(m, src, "", [])
    assert "## __mkapi__.mkapi.objects.LINK_PATTERN\nLINK_PATTERN = re" in m

    es = ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]
    h = markdown.markdown(m, extensions=es)
    assert '<span class="c1">## __mkapi__.mkapi.objects.is_empty</span>' in h
    h = convert_source(h, Path(src), "XXX")
    assert '<span id="mkapi.objects.is_empty" class="mkapi-docs-link">' in h
    assert '<a href="../../api/a/#mkapi.objects.is_empty">[XXX]</a></span>' in h
