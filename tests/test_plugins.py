import importlib.util
from pathlib import Path

import pytest
from jinja2.environment import Environment
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import PluginCollection
from mkdocs.theme import Theme

import mkapi
from mkapi.plugins import (
    MkAPIConfig,
    MkAPIPlugin,
    _collect,
    _create_nav,
    _get_path_module_name_filters,
    _insert_sys_path,
    _on_config_plugin,
    _walk_nav,
)


@pytest.fixture(scope="module")
def config_file():
    return Path(mkapi.__file__).parent.parent.parent / "examples" / "mkdocs.yml"


def test_config_file_exists(config_file: Path):
    assert config_file.exists()


def test_themes_templates_exists():
    for path in ["themes", "templates"]:
        assert (Path(mkapi.__file__).parent / path).exists()


@pytest.fixture(scope="module")
def mkdocs_config(config_file: Path):
    return load_config(str(config_file))


def test_mkdocs_config(mkdocs_config: MkDocsConfig):
    config = mkdocs_config
    assert isinstance(config, MkDocsConfig)
    path = Path(config.config_file_path)
    assert path.as_posix().endswith("mkapi/examples/mkdocs.yml")
    assert config.site_name == "Doc for CI"
    assert Path(config.docs_dir) == path.parent / "docs"
    assert Path(config.site_dir) == path.parent / "site"
    assert config.nav[0] == "index.md"  # type: ignore
    assert isinstance(config.plugins, PluginCollection)
    assert isinstance(config.plugins["mkapi"], MkAPIPlugin)
    assert config.pages is None
    assert isinstance(config.theme, Theme)
    assert config.theme.name == "mkdocs"
    assert isinstance(config.theme.get_env(), Environment)
    assert config.extra_css == ["custom.css"]
    assert str(config.extra_javascript[0]).endswith("tex-mml-chtml.js")
    assert "pymdownx.arithmatex" in config.markdown_extensions


@pytest.fixture(scope="module")
def mkapi_plugin(mkdocs_config: MkDocsConfig):
    return mkdocs_config.plugins["mkapi"]


def test_mkapi_plugin(mkapi_plugin: MkAPIPlugin):
    assert isinstance(mkapi_plugin, MkAPIPlugin)
    assert mkapi_plugin.server is None
    assert isinstance(mkapi_plugin.config, MkAPIConfig)


@pytest.fixture(scope="module")
def mkapi_config(mkapi_plugin: MkAPIPlugin):
    return mkapi_plugin.config


def test_mkapi_config(mkapi_config: MkAPIConfig):
    config = mkapi_config
    assert config.src_dirs == ["."]
    assert config.on_config == "custom.on_config"
    assert config.filters == ["plugin_filter"]
    assert config.exclude == [".tests"]
    assert config.abs_api_paths == []


def test_insert_sys_path(mkapi_config: MkAPIConfig):
    assert not importlib.util.find_spec("custom")
    _insert_sys_path(mkapi_config)
    spec = importlib.util.find_spec("custom")
    assert spec
    assert spec.origin
    assert spec.origin.endswith("custom.py")


def test_on_config_plugin(mkdocs_config, mkapi_plugin):
    config = _on_config_plugin(mkdocs_config, mkapi_plugin)
    assert mkdocs_config is config


@pytest.fixture(scope="module")
def nav(mkdocs_config: MkDocsConfig):
    return mkdocs_config.nav


def test_nav_before_update(nav):
    assert isinstance(nav, list)
    assert nav[0] == "index.md"
    assert nav[1] == "<api>/mkapi.objects|nav_filter1|nav_filter2"
    assert nav[2] == {"Section": ["1.md", "<api2>/mkapi|nav_filter3", "2.md"]}
    assert nav[3] == {"API": "<api>/mkdocs|nav_filter4"}


def test_walk_nav(nav):
    def create_pages(item: str) -> list:
        print(item)
        items.append(item.split("|")[-1])
        if item.endswith("filter4"):
            return ["a"]
        return ["b", "c"]

    items = []
    nav = _walk_nav(nav, create_pages)
    assert items == ["nav_filter2", "nav_filter3", "nav_filter4"]
    assert isinstance(nav, list)
    assert nav[1:3] == ["b", "c"]
    assert nav[3] == {"Section": ["1.md", "b", "c", "2.md"]}
    assert nav[4] == {"API": "a"}


def test_get_path_module_name_filters():
    p, m, f = _get_path_module_name_filters("<api>/a.b|f1|f2", ["f"])
    assert p == "api"
    assert m == "a.b"
    assert f == ["f", "f1", "f2"]
    p, m, f = _get_path_module_name_filters("<api>/a", ["f"])
    assert p == "api"
    assert m == "a"
    assert f == ["f"]


def test_create_nav():
    def callback(name):
        return {name.upper(): f"test/{name}.md"}

    def section(name):
        return name.replace(".", "-")

    f = _create_nav
    a = [{"MKDOCS.PLUGINS": "test/mkdocs.plugins.md"}]
    assert f("mkdocs.plugins", callback) == a
    a = [{"MKDOCS.LIVERELOAD": "test/mkdocs.livereload.md"}]
    assert f("mkdocs.livereload", callback) == a
    nav = f("mkdocs.commands", callback)
    assert nav[0] == {"MKDOCS.COMMANDS": "test/mkdocs.commands.md"}
    assert nav[-1] == {"MKDOCS.COMMANDS.SERVE": "test/mkdocs.commands.serve.md"}
    nav = f("mkdocs", callback, section, lambda x: "tests" not in x)
    assert len(nav[1]) == 1
    assert "mkdocs-commands" in nav[1]


def test_collect(mkdocs_config: MkDocsConfig):
    def create_page(name: str, path: Path, filters: list[str]) -> None:
        assert "mkapi" in name
        assert "examples" in path.as_posix()
        assert filters == ["A", "F", "G"]

    docs_dir = mkdocs_config.docs_dir
    nav, paths = _collect("<a/b/c>/mkapi|F|G", docs_dir, ["A"], create_page)
    assert nav[0] == {"mkapi": "a/b/c/mkapi.md"}


# def test_walk_module_tree():
#     tree = find_submodule_tree("mkdocs", )
#     _walk_module_tree(tree)
#     assert 0


# def test_collect(mkdocs_config: MkDocsConfig):
#     docs_dir = mkdocs_config.docs_dir
#     assert 0


# @pytest.fixture(scope="module")
# def env(mkdocs_config: MkDocsConfig):
#     return mkdocs_config.theme.get_env()


# def test_mkdocs_build(mkdocs_config: MkDocsConfig):
#     config = mkdocs_config
#     config.plugins.on_startup(command="build", dirty=False)
#     try:
#         build(config, dirty=False)
#     finally:
#         config.plugins.on_shutdown()
