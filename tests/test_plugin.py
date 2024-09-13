# import os
# import shutil
# import sys
# from pathlib import Path

# import pytest
# from jinja2.environment import Environment
# from mkdocs.commands.build import build
# from mkdocs.config import load_config
# from mkdocs.config.defaults import MkDocsConfig
# from mkdocs.plugins import PluginCollection
# from mkdocs.structure.files import Files
# from mkdocs.theme import Theme

# import mkapi
# from mkapi.plugin import (
#     MkAPIConfig,
#     MkAPIPlugin,
#     _build_apinav,
#     _collect_stylesheets,
#     _get_function,
#     _update_extensions,
#     _update_nav,
#     _update_templates,
# )
# from mkapi.renderer import templates
# from mkapi.utils import get_module_path, module_cache


# @pytest.fixture(scope="module")
# def config_file():
#     return Path(__file__).parent.parent / "mkdocs.yml"


# def test_config_file_exists(config_file: Path):
#     assert config_file.exists()


# def test_assets():
#     for path in ["stylesheets", "templates"]:
#         assert (Path(mkapi.__file__).parent / path).exists()


# @pytest.fixture(scope="module")
# def mkdocs_config(config_file: Path):
#     return load_config(str(config_file))


# def test_mkdocs_config(mkdocs_config: MkDocsConfig):
#     config = mkdocs_config
#     assert isinstance(config, MkDocsConfig)
#     path = Path(config.config_file_path)
#     assert path.as_posix().endswith("mkapi/mkdocs.yml")
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


# def test_nav(mkdocs_config: MkDocsConfig):
#     nav = mkdocs_config.nav
#     assert nav
#     nav_dict = {}
#     for item in nav:
#         if isinstance(item, dict):
#             nav_dict.update(item)
#     assert "Usage" in nav_dict
#     assert nav_dict["API"] == "$api:src/mkapi.**"
#     assert nav_dict["Examples"] == "$api:src/examples.**"
#     assert "Schemdraw" not in nav_dict
#     assert "Polars" not in nav_dict
#     assert "Altair" not in nav_dict


# @pytest.fixture(scope="module")
# def mkapi_plugin(mkdocs_config: MkDocsConfig):
#     return mkdocs_config.plugins["mkapi"]


# def test_mkapi_plugin(mkapi_plugin: MkAPIPlugin):
#     assert isinstance(mkapi_plugin, MkAPIPlugin)
#     assert isinstance(mkapi_plugin.config, MkAPIConfig)


# @pytest.fixture(scope="module")
# def mkapi_config(mkapi_plugin: MkAPIPlugin):
#     return mkapi_plugin.config


# def test_mkapi_config(mkapi_config: MkAPIConfig):
#     config = mkapi_config
#     assert config.config == "config.py"
#     assert config.debug is True


# def test_get_function(mkapi_plugin):
#     assert _get_function("before_on_config", mkapi_plugin)
#     assert _get_function("after_on_config", mkapi_plugin)
#     assert _get_function("page_title", mkapi_plugin)
#     assert _get_function("section_title", mkapi_plugin)
#     assert _get_function("toc_title", mkapi_plugin)


# @pytest.fixture
# def config_plugin(tmpdir):
#     dest = Path(tmpdir)
#     root = Path(__file__).parent.parent
#     config_file = root / "mkdocs.yml"
#     shutil.copy(config_file, dest)
#     for src in ["docs", "src", "tests"]:
#         src_dir = root / src
#         shutil.copytree(src_dir, dest / src)
#     curdir = Path(os.curdir).absolute()
#     os.chdir(dest)
#     sys.path.insert(0, ".")
#     config = load_config("mkdocs.yml")
#     plugin = config.plugins["mkapi"]
#     assert isinstance(plugin, MkAPIPlugin)
#     plugin.__init__()
#     yield config, plugin
#     config.plugins.on_shutdown()
#     sys.path.pop(0)
#     os.chdir(curdir)


# @pytest.fixture
# def config(config_plugin):
#     return config_plugin[0]


# def test_update_templates(config_plugin: tuple[MkDocsConfig, MkAPIPlugin]):
#     config, plugin = config_plugin
#     _update_templates(config, plugin)
#     for x in ["document", "header", "heading", "object", "source"]:
#         assert x in templates


# def test_update_extensions(config_plugin: tuple[MkDocsConfig, MkAPIPlugin]):
#     config, plugin = config_plugin
#     _update_extensions(config, plugin)
#     for x in ["admonition", "md_in_html"]:
#         assert x in config.markdown_extensions


# def test_create_nav(config_plugin: tuple[MkDocsConfig, MkAPIPlugin]):
#     config, plugin = config_plugin
#     _build_apinav(config, plugin)
#     docs_dir = Path(config.docs_dir)
#     for x in ["api", "src"]:
#         assert (docs_dir / x).exists()

#     assert str(get_module_path("mkapi").parent) in config.watch  # type: ignore
#     assert len(plugin.api_dirs) == 2


# def test_on_config(config_plugin: tuple[MkDocsConfig, MkAPIPlugin]):
#     config, plugin = config_plugin
#     plugin.on_config(config)
#     nav = config.nav
#     assert nav
#     assert isinstance(nav[2]["API"], list)
#     path = "api/mkapi/README.md"
#     assert nav[2]["API"][0]["mkapi"] == path

#     docs_dir = Path(config.docs_dir)
#     for x in ["api/mkapi", "api/examples", "src/mkapi", "src/examples"]:
#         assert (docs_dir / x).exists()

#     assert "api/mkapi/README.md" in plugin.pages
#     assert "src/examples/styles/google.md" in plugin.pages


# def test_create_page(config_plugin: tuple[MkDocsConfig, MkAPIPlugin]):
#     config, plugin = config_plugin
#     plugin.on_config(config)
#     for path in ["api/mkapi/README.md", "api/mkapi/objects.md", "api/mkapi/nodes.md"]:
#         assert (Path(config.docs_dir) / path).exists()
#         if "READ" not in path:
#             assert (Path(config.docs_dir) / path.replace("api/m", "src/m")).exists()


# def test_collect_stylesheets(config: MkDocsConfig):
#     plugin = config.plugins["mkapi"]
#     assert isinstance(plugin, MkAPIPlugin)
#     files = Files(_collect_stylesheets(config, plugin))
#     assert files.media_files()


# # @pytest.mark.parametrize("dirty", [False, True])
# # def test_build(config: MkDocsConfig, dirty):
# #     config.plugins.on_startup(command="build", dirty=dirty)
# #     plugin = config.plugins["mkapi"]
# #     assert isinstance(plugin, MkAPIPlugin)
# #     assert not plugin.pages
# #     assert plugin.dirty is dirty
# #     build(config, dirty=dirty)
# #     for x in ["mkapi", "examples"]:
# #         assert os.listdir(f"docs/api/{x}")
# #         assert os.listdir(f"docs/src/{x}")
# #     pages = plugin.pages
# #     assert not pages["usage/object.md"].markdown
# #     page = pages["api/examples/styles/README.md"]
# #     m = page.convert_markdown("", {"object": "ABC", "source": "DEF"})
# #     assert '[example](../README.md#examples "examples")' in m
# #     assert "[[ABC]](../../../src/examples/styles.md#example._styles" in m
# #     assert "[ExampleClassGoogle](google.md#example._styles.ExampleClassGoogle" in m
# #     page = pages["src/examples/styles/google.md"]
# #     m = page.markdown
# #     assert "## ::: example._styles.google.ExampleError|__mkapi__" in m
# #     assert ":example._styles.google.ExampleError=152" in m
# #     m = page.convert_markdown("", {"object": "ABC", "source": "DEF"})
# #     assert "class ExamplePEP526Class:## __mkapi__.example" in m
# #     assert 'ExampleClass.__special__" markdown="1">' in m


# # def test_update_markdown_for_dirty_module(config: MkDocsConfig):
# #     module_cache.clear()
# #     sys.path.insert(0, ".")
# #     config.nav = [{"API": "$x:y/AAA"}]

# #     with Path("AAA.py").open("w") as f:
# #         f.write("'''abc123'''")
# #     assert get_module_path("AAA") == Path("AAA.py").absolute()

# #     plugin = config.plugins["mkapi"]
# #     assert isinstance(plugin, MkAPIPlugin)
# #     config.plugins.on_startup(command="build", dirty=True)
# #     build(config, dirty=True)

# #     path_docs = "x/AAA.md"
# #     path_src = "y/AAA.md"
# #     with (Path("docs") / path_docs).open() as f:
# #         ts1 = f.read()
# #     with (Path("docs") / path_src).open() as f:
# #         ts2 = f.read()
# #     m = plugin.pages[path_docs].convert_markdown("", {"source": "a"})
# #     assert "\nabc123\n" in m
# #     m = plugin.pages[path_src].convert_markdown("", {"object": "a"})
# #     assert "'''abc123'''\n" in m

# #     with Path("AAA.py").open("w") as f:
# #         f.write("'''def456'''")

# #     build(config, dirty=True)

# #     with (Path("docs") / path_docs).open() as f:
# #         ts3 = f.read()
# #     with (Path("docs") / path_src).open() as f:
# #         ts4 = f.read()
# #     m = plugin.pages[path_docs].convert_markdown("", {"source": "a"})
# #     assert "\ndef456\n" in m
# #     m = plugin.pages[path_src].convert_markdown("", {"object": "a"})
# #     assert "'''def456'''\n" in m
# #     assert ts1 != ts3
# #     assert ts2 != ts4

# #     sys.path.pop(0)
