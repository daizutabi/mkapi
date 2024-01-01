from pathlib import Path

import pytest
from jinja2.environment import Environment
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import PluginCollection
from mkdocs.theme import Theme

from mkapi.plugins import MkAPIConfig, MkAPIPlugin


@pytest.fixture(scope="module")
def config_file():
    return Path(__file__).parent.parent / "examples" / "mkdocs.yml"


def test_config_file_exists(config_file: Path):
    assert config_file.exists()


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
    assert mkapi_plugin.server is None
    assert isinstance(mkapi_plugin.config, MkAPIConfig)


@pytest.fixture(scope="module")
def mkapi_config(mkapi_plugin: MkAPIPlugin):
    return mkapi_plugin.config


def test_mkapi_config(mkapi_config: MkAPIConfig):
    config = mkapi_config
    x = ["src_dirs", "on_config", "filters", "callback", "abs_api_paths", "pages"]
    assert list(config) == x
    assert config.src_dirs == ["."]
    assert config.on_config == "custom.on_config"


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
