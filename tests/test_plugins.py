# import importlib.util
# from pathlib import Path

# import pytest
# from jinja2.environment import Environment
# from mkdocs.config import load_config
# from mkdocs.config.defaults import MkDocsConfig
# from mkdocs.plugins import PluginCollection
# from mkdocs.theme import Theme

# import mkapi
# from mkapi.plugins import (
#     MkAPIConfig,
#     MkAPIPlugin,
#     _insert_sys_path,
# )


# @pytest.fixture(scope="module")
# def config_file():
#     return Path(__file__).parent / "examples" / "mkdocs.yml"


# def test_config_file_exists(config_file: Path):
#     print(config_file)
#     assert config_file.exists()


# def test_themes_templates_exists():
#     for path in ["themes", "templates"]:
#         assert (Path(mkapi.__file__).parent / path).exists()


# @pytest.fixture(scope="module")
# def mkdocs_config(config_file: Path):
#     return load_config(str(config_file))


# def test_mkdocs_config(mkdocs_config: MkDocsConfig):
#     config = mkdocs_config
#     assert isinstance(config, MkDocsConfig)
#     path = Path(config.config_file_path)
#     assert path.as_posix().endswith("mkapi/examples/mkdocs.yml")
#     assert config.site_name == "MkAPI"
#     assert Path(config.docs_dir) == path.parent / "docs"
#     assert Path(config.site_dir) == path.parent / "site"
#     assert config.nav[0] == "index.md"  # type: ignore
#     assert isinstance(config.plugins, PluginCollection)
#     assert isinstance(config.plugins["mkapi"], MkAPIPlugin)
#     assert config.pages is None
#     assert isinstance(config.theme, Theme)
#     assert config.theme.name == "material"
#     assert isinstance(config.theme.get_env(), Environment)


# @pytest.fixture(scope="module")
# def mkapi_plugin(mkdocs_config: MkDocsConfig):
#     return mkdocs_config.plugins["mkapi"]


# def test_mkapi_plugin(mkapi_plugin: MkAPIPlugin):
#     assert isinstance(mkapi_plugin, MkAPIPlugin)
#     assert mkapi_plugin.nav is None
#     assert isinstance(mkapi_plugin.config, MkAPIConfig)


# @pytest.fixture(scope="module")
# def mkapi_config(mkapi_plugin: MkAPIPlugin):
#     return mkapi_plugin.config


# def test_mkapi_config(mkapi_config: MkAPIConfig):
#     config = mkapi_config
#     assert config.filters == ["plugin_filter"]
#     assert config.exclude == [".tests"]


# def test_insert_sys_path(mkdocs_config, mkapi_plugin):
#     assert not importlib.util.find_spec("custom")
#     _insert_sys_path(mkdocs_config, mkapi_plugin)
#     spec = importlib.util.find_spec("custom")
#     assert spec
#     assert spec.origin
#     assert spec.origin.endswith("custom.py")
