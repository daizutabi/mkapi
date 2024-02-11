import shutil
from pathlib import Path

import pytest
from jinja2.environment import Environment
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import PluginCollection
from mkdocs.structure.files import Files
from mkdocs.theme import Theme

import mkapi
from mkapi.plugins import MkAPIConfig, MkAPIPlugin, _collect_stylesheets, _get_function


@pytest.fixture(scope="module")
def config_file():
    return Path(__file__).parent.parent / "mkdocs.yml"


def test_config_file_exists(config_file: Path):
    assert config_file.exists()


def test_assets():
    for path in ["stylesheets", "templates"]:
        assert (Path(mkapi.__file__).parent / path).exists()


@pytest.fixture(scope="module")
def mkdocs_config(config_file: Path):
    return load_config(str(config_file))


def test_mkdocs_config(mkdocs_config: MkDocsConfig):
    config = mkdocs_config
    assert isinstance(config, MkDocsConfig)
    path = Path(config.config_file_path)
    assert path.as_posix().endswith("mkapi/mkdocs.yml")
    assert config.site_name == "MkAPI"
    assert Path(config.docs_dir) == path.parent / "docs"
    assert Path(config.site_dir) == path.parent / "site"
    assert config.nav[0] == "index.md"  # type: ignore
    assert isinstance(config.plugins, PluginCollection)
    assert isinstance(config.plugins["mkapi"], MkAPIPlugin)
    assert config.pages is None
    assert isinstance(config.theme, Theme)
    assert config.theme.name == "material"
    assert isinstance(config.theme.get_env(), Environment)


def test_nav(mkdocs_config: MkDocsConfig):
    nav = mkdocs_config.nav
    assert nav
    nav_dict = {}
    for item in nav:
        if isinstance(item, dict):
            nav_dict.update(item)
    assert "Usage" in nav_dict
    assert nav_dict["API"] == "$api:src/mkapi.**"
    assert nav_dict["Examples"] == "$api:src/examples.**"
    assert "Schemdraw" not in nav_dict
    assert "Polars" not in nav_dict
    assert "Altair" not in nav_dict


@pytest.fixture(scope="module")
def mkapi_plugin(mkdocs_config: MkDocsConfig):
    return mkdocs_config.plugins["mkapi"]


def test_mkapi_plugin(mkapi_plugin: MkAPIPlugin):
    assert isinstance(mkapi_plugin, MkAPIPlugin)
    assert isinstance(mkapi_plugin.config, MkAPIConfig)


@pytest.fixture(scope="module")
def mkapi_config(mkapi_plugin: MkAPIPlugin):
    return mkapi_plugin.config


def test_mkapi_config(mkapi_config: MkAPIConfig):
    config = mkapi_config
    assert config.config == "config.py"
    assert config.debug is True


def test_get_function(mkapi_plugin):
    assert _get_function("before_on_config", mkapi_plugin)
    assert _get_function("after_on_config", mkapi_plugin)
    assert _get_function("page_title", mkapi_plugin)
    assert _get_function("section_title", mkapi_plugin)
    assert _get_function("toc_title", mkapi_plugin)


@pytest.fixture(scope="module")
def config(mkdocs_config: MkDocsConfig, mkapi_plugin: MkAPIPlugin):
    api_dir = Path(mkdocs_config.docs_dir) / "api"
    src_dir = Path(mkdocs_config.docs_dir) / "src"
    site_dir = Path(mkdocs_config.site_dir)
    assert not api_dir.exists()
    assert not src_dir.exists()
    if site_dir.exists():
        shutil.rmtree(site_dir)
    yield mkdocs_config
    mkapi_plugin.on_shutdown()
    assert not api_dir.exists()
    assert not src_dir.exists()
    if site_dir.exists():
        shutil.rmtree(site_dir)


def test_on_config(config: MkDocsConfig, mkapi_plugin: MkAPIPlugin):
    config = mkapi_plugin.on_config(config)
    nav = config.nav
    assert nav
    assert isinstance(nav[2]["API"], list)
    path = "api/mkapi/README.md"
    assert nav[2]["API"][0]["mkapi"] == path
    for path in ["api/mkapi/README.md", "api/mkapi/objects.md", "api/mkapi/items.md"]:
        assert (Path(config.docs_dir) / path).exists()
        if "READ" not in path:
            assert (Path(config.docs_dir) / path.replace("api/m", "src/m")).exists()
    path = "src/mkapi.md"
    assert (Path(config.docs_dir) / path).exists()


def test_collect_stylesheets(config: MkDocsConfig, mkapi_plugin: MkAPIPlugin):
    files = Files(_collect_stylesheets(config, mkapi_plugin))
    assert files.media_files()


def test_build(config: MkDocsConfig):
    assert build(config) is None
    plugin = config.plugins["mkapi"]
    assert isinstance(plugin, MkAPIPlugin)
    pages = plugin.pages
    assert not pages["usage/object.md"].markdown
    page = pages["api/examples/styles/README.md"]
    assert page.markdown == "# ::: examples.styles\n"
    m = page.convert_markdown("", "ABC")
    assert '[examples](../README.md#examples "examples")' in m
    assert "[[ABC]](../../../src/examples/styles.md#examples.styles" in m
    assert "[ExampleClassGoogle](google.md#examples.styles.google.ExampleClass" in m
