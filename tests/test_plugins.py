import importlib.util
from pathlib import Path

import pytest
from jinja2.environment import Environment
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import PluginCollection
from mkdocs.theme import Theme

import mkapi
from mkapi.plugins import (
    MkAPIConfig,
    MkAPIPlugin,
    _insert_sys_path,
    _on_config_plugin,
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
    assert config.theme.name == "material"
    assert isinstance(config.theme.get_env(), Environment)
    assert config.extra_css == ["custom.css"]
    assert str(config.extra_javascript[0]).endswith("tex-mml-chtml.js")
    assert "pymdownx.arithmatex" in config.markdown_extensions


@pytest.fixture(scope="module")
def mkapi_plugin(mkdocs_config: MkDocsConfig):
    return mkdocs_config.plugins["mkapi"]


def test_mkapi_plugin(mkapi_plugin: MkAPIPlugin):
    assert isinstance(mkapi_plugin, MkAPIPlugin)
    assert mkapi_plugin.nav is None
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
