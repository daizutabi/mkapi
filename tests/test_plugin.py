import os
import shutil
import sys
from pathlib import Path

import pytest
from astdoc.utils import get_module_path
from jinja2.environment import Environment
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import PluginCollection
from mkdocs.theme import Theme

import mkapi
from mkapi.plugin import Config, Plugin


@pytest.fixture(scope="module")
def config_file():
    return Path(__file__).parent.parent / "mkdocs.yaml"


def test_config_file_exists(config_file: Path):
    assert config_file.exists()


def test_assets():
    for path in ["css", "javascript", "templates"]:
        assert (Path(mkapi.__file__).parent / path).exists()


@pytest.fixture(scope="module")
def mkdocs_config(config_file: Path):
    return load_config(str(config_file))


def test_mkdocs_config(mkdocs_config: MkDocsConfig):
    config = mkdocs_config
    assert isinstance(config, MkDocsConfig)
    path = Path(config.config_file_path)
    assert path.as_posix().endswith("mkapi/mkdocs.yaml")
    assert config.site_name == "MkAPI"
    assert Path(config.docs_dir) == path.parent / "docs"
    assert Path(config.site_dir) == path.parent / "site"
    assert config.nav[0] == {"Home": "index.md"}  # type: ignore
    assert isinstance(config.plugins, PluginCollection)
    assert isinstance(config.plugins["mkapi"], Plugin)
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
    assert nav_dict["API Reference"] == ["$api:src/mkapi.***"]
    assert nav_dict["Example"] == "$api:src/example.***"


@pytest.fixture(scope="module")
def mkapi_plugin(mkdocs_config: MkDocsConfig):
    return mkdocs_config.plugins["mkapi"]


def test_mkapi_plugin(mkapi_plugin: Plugin):
    assert isinstance(mkapi_plugin, Plugin)
    assert isinstance(mkapi_plugin.config, Config)


@pytest.fixture(scope="module")
def mkapi_config(mkapi_plugin: Plugin):
    return mkapi_plugin.config


def test_mkapi_config(mkapi_config: Config):
    config = mkapi_config
    assert config.config == "config.py"
    assert config.debug is True
    assert config.exclude == ["_example"]


@pytest.fixture
def config_plugin(tmp_path):
    dest = Path(tmp_path)
    root = Path(__file__).parent.parent
    config_file = root / "mkdocs.yaml"
    shutil.copy(config_file, dest)
    for src in ["docs", "src", "tests"]:
        src_dir = root / src
        shutil.copytree(src_dir, dest / src)
    curdir = Path(os.curdir).absolute()
    os.chdir(dest)
    sys.path.insert(0, ".")
    config = load_config("mkdocs.yaml")
    plugin = config.plugins["mkapi"]
    assert isinstance(plugin, Plugin)
    plugin.__init__()

    yield config, plugin

    config.plugins.on_shutdown()
    sys.path.pop(0)
    os.chdir(curdir)


@pytest.fixture
def config(config_plugin):
    return config_plugin[0]


def test_update_extensions(config: MkDocsConfig):
    from mkapi.plugin import _update_extensions

    _update_extensions(config)
    for x in ["admonition", "md_in_html"]:
        assert x in config.markdown_extensions


def test_build_apinav(config: MkDocsConfig):
    from mkapi.plugin import _build_apinav

    _build_apinav(config)

    assert str(get_module_path("mkapi").parent) in config.watch  # type: ignore


def test_on_config(config_plugin: tuple[MkDocsConfig, Plugin]):
    config, plugin = config_plugin
    plugin.on_config(config)
    nav = config.nav
    assert nav
    assert isinstance(nav[2]["API Reference"], list)
    path = "api/mkapi/README.md"
    assert nav[2]["API Reference"][0]["mkapi"][0]["mkapi"] == path
    assert "api/mkapi/README.md" in plugin.pages
    assert "src/example/mod_a.md" in plugin.pages
    assert "src/example/sub/mod_b.md" in plugin.pages


@pytest.mark.parametrize("dirty", [False, True])
def test_build(config: MkDocsConfig, dirty: bool):
    from mkapi.config import get_config, get_function

    config.plugins.on_startup(command="build", dirty=dirty)
    plugin = config.plugins["mkapi"]
    assert isinstance(plugin, Plugin)
    assert not plugin.pages

    build(config, dirty=dirty)

    assert get_function("before_on_config")
    assert get_function("after_on_config")
    assert get_function("page_title")
    assert get_function("section_title")
    assert get_function("toc_title")

    assert len(config.extra_css) == 3
    assert len(config.extra_javascript) == 1

    pages = plugin.pages
    assert pages["usage/object.md"].is_documentation_page()
    assert pages["api/mkapi/page.md"].is_object_page()
    assert pages["src/mkapi/page.md"].is_source_page()

    assert plugin.config.debug is True

    mkapi_config = get_config()
    assert mkapi_config is plugin.config
    assert mkapi_config.debug is True
