"""MkAPI Plugin class.

MkAPI Plugin is a MkDocs plugin that creates Python API documentation
from Docstring.
"""
from __future__ import annotations

import atexit
import inspect
import logging
import os
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeGuard

import yaml
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.livereload import LiveReloadServer
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files, get_files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page as MkDocsPage
from mkdocs.structure.toc import AnchorLink, TableOfContents
from mkdocs.utils.templates import TemplateContext

import mkapi.config
from mkapi.filter import split_filters, update_filters

# from mkapi.modules import Module, get_module

# from mkapi.core.module import Module, get_module
# from mkapi.core.object import get_object
# from mkapi.core.page import Page as MkAPIPage

logger = logging.getLogger("mkdocs")
global_config = {}


class MkAPIConfig(Config):
    """Specify the config schema."""

    src_dirs = config_options.Type(list, default=[])
    on_config = config_options.Type(str, default="")
    filters = config_options.Type(list, default=[])
    callback = config_options.Type(str, default="")
    abs_api_paths = config_options.Type(list, default=[])
    pages = config_options.Type(dict, default={})


class MkAPIPlugin(BasePlugin[MkAPIConfig]):
    """MkAPIPlugin class for API generation."""

    server = None

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:  # noqa: ARG002, D102
        _insert_sys_path(self.config)
        _update_config(config, self)
        if "admonition" not in config.markdown_extensions:
            config.markdown_extensions.append("admonition")
        return _on_config_plugin(config, self)

    #     def on_files(self, files: Files, config: MkDocsConfig, **kwargs) -> Files:  # noqa: ARG002
    #         """Collect plugin CSS/JavaScript and appends them to `files`."""
    #         root = Path(mkapi.__file__).parent / "theme"
    #         docs_dir = config.docs_dir
    #         config.docs_dir = root.as_posix()
    #         theme_files = get_files(config)
    #         config.docs_dir = docs_dir
    #         theme_name = config.theme.name or "mkdocs"

    #         css = []
    #         js = []
    #         for file in theme_files:
    #             path = Path(file.src_path).as_posix()
    #             if path.endswith(".css"):
    #                 if "common" in path or theme_name in path:
    #                     files.append(file)
    #                     css.append(path)
    #             elif path.endswith(".js"):
    #                 files.append(file)
    #                 js.append(path)
    #             elif path.endswith(".yml"):
    #                 with (root / path).open() as f:
    #                     data = yaml.safe_load(f)
    #                 css = data.get("extra_css", []) + css
    #                 js = data.get("extra_javascript", []) + js
    #         css = [x for x in css if x not in config.extra_css]
    #         js = [x for x in js if x not in config.extra_javascript]
    #         config.extra_css.extend(css)
    #         config.extra_javascript.extend(js)

    #         return files

    #     def on_page_markdown(
    #         self,
    #         markdown: str,
    #         page: MkDocsPage,
    #         config: MkDocsConfig,  # noqa: ARG002
    #         files: Files,  # noqa: ARG002
    #         **kwargs,  # noqa: ARG002
    #     ) -> str:
    #         """Convert Markdown source to intermidiate version."""
    #         abs_src_path = page.file.abs_src_path
    #         clean_page_title(page)
    #         abs_api_paths = self.config.abs_api_paths
    #         filters = self.config.filters
    #         mkapi_page = MkAPIPage(markdown, abs_src_path, abs_api_paths, filters)
    #         self.config.pages[abs_src_path] = mkapi_page
    #         return mkapi_page.markdown

    #     def on_page_content(
    #         self,
    #         html: str,
    #         page: MkDocsPage,
    #         config: MkDocsConfig,  # noqa: ARG002
    #         files: Files,  # noqa: ARG002
    #         **kwargs,  # noqa: ARG002
    #     ) -> str:
    #         """Merge HTML and MkAPI's node structure."""
    #         if page.title:
    #             page.title = re.sub(r"<.*?>", "", str(page.title))  # type: ignore
    #         abs_src_path = page.file.abs_src_path
    #         mkapi_page: MkAPIPage = self.config.pages[abs_src_path]
    #         return mkapi_page.content(html)

    #     def on_page_context(
    #         self,
    #         context: TemplateContext,
    #         page: MkDocsPage,
    #         config: MkDocsConfig,  # noqa: ARG002
    #         nav: Navigation,  # noqa: ARG002
    #         **kwargs,  # noqa: ARG002
    #     ) -> TemplateContext:
    #         """Clear prefix in toc."""
    #         abs_src_path = page.file.abs_src_path
    #         if abs_src_path in self.config.abs_api_paths:
    #             clear_prefix(page.toc, 2)
    #         else:
    #             mkapi_page: MkAPIPage = self.config.pages[abs_src_path]
    #             for level, id_ in mkapi_page.headings:
    #                 clear_prefix(page.toc, level, id_)
    #         return context

    def on_serve(  # noqa: D102
        self,
        server: LiveReloadServer,
        config: MkDocsConfig,  # noqa: ARG002
        builder: Callable,
        **kwargs,  # noqa: ARG002
    ) -> LiveReloadServer:
        # for path in ["theme", "templates"]:
        #     path_str = (Path(mkapi.__file__).parent / path).as_posix()
        #     server.watch(path_str, builder)
        self.__class__.server = server
        return server


def _insert_sys_path(config: MkAPIConfig) -> None:
    config_dir = Path(config.config_file_path).parent
    for src_dir in config.src_dirs:
        if (path := os.path.normpath(config_dir / src_dir)) not in sys.path:
            sys.path.insert(0, path)
    if not config.src_dirs and (path := Path.cwd()) not in sys.path:
        sys.path.insert(0, str(path))


def _update_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not plugin.server:
        plugin.config.abs_api_paths = _update_nav(config, plugin.config.filters)
        global_config["nav"] = config.nav
        global_config["abs_api_paths"] = plugin.config.abs_api_paths
    else:
        config.nav = global_config["nav"]
        plugin.config.abs_api_paths = global_config["abs_api_paths"]


def _update_nav(config: MkDocsConfig, filters: list[str]) -> list[Path]:
    if not isinstance(config.nav, list):
        return []

    def create_api_nav(item: str) -> list:
        nav, paths = _collect(item, config.docs_dir, filters)
        abs_api_paths.extend(paths)
        return nav

    abs_api_paths: list[Path] = []
    _walk_nav(config.nav, create_api_nav)
    print("AAAAAAAAAAAAAAAAAAA\n", config.nav)
    abs_api_paths = list(set(abs_api_paths))
    return abs_api_paths


def _walk_nav(nav: list | dict, create_api_nav: Callable[[str], list]) -> None:
    print("DDD", nav)
    it = enumerate(nav) if isinstance(nav, list) else nav.items()
    for k, item in it:
        if _is_api_entry(item):
            api_nav = create_api_nav(item)
            print("EEE", k, api_nav, type(nav))
            # nav[k] = api_nav if isinstance(nav, dict) else {item: api_nav}
            nav[k] = {"AAAA": [api_nav]}
            print("FFF", nav)
        elif isinstance(item, list | dict):
            _walk_nav(item, create_api_nav)


API_URL_PATTERN = re.compile(r"^\<(.+)\>/(.+)$")


def _is_api_entry(item: str | list | dict) -> TypeGuard[str]:
    return isinstance(item, str) and re.match(API_URL_PATTERN, item) is not None


def _collect(item: str, docs_dir: str, filters: list[str]) -> tuple[list, list[Path]]:
    """Collect modules."""
    if not (m := re.match(API_URL_PATTERN, item)):
        raise NotImplementedError
    api_path, module_name = m.groups()
    abs_api_path = Path(docs_dir) / api_path
    Path.mkdir(abs_api_path, parents=True, exist_ok=True)
    module_name, filters_ = split_filters(module_name)
    filters = update_filters(filters, filters_)

    def add_module(module: Module, package: str | None) -> None:
        module_path = module.name + ".md"
        abs_module_path = abs_api_path / module_path
        abs_api_paths.append(abs_module_path)
        _create_page(abs_module_path, module, filters)
        module_name = module.name
        if package and "short_nav" in filters and module_name != package:
            module_name = module_name[len(package) + 1 :]
        modules[module_name] = (Path(api_path) / module_path).as_posix()
        # abs_source_path = abs_api_path / "source" / module_path
        # create_source_page(abs_source_path, module, filters)

    abs_api_paths: list[Path] = []
    modules: dict[str, str] = {}
    nav, package = [], None
    module = get_module(module_name)
    print(module.get_tree())
    add_module(module, None)
    nav = modules

    # if not module.is_package():
    #     pass  # TODO

    # for module in get_module(module_name):
    #     if module.is_package():
    #         if package and modules:
    #             nav.append({package: modules})
    #         package = module.name
    #         modules = {}
    #         add_module(module, package)  # Skip if no docstring.
    #     else:
    #         add_module(module, package)
    # if package and modules:
    #     nav.append({package: modules})
    # if modules:
    #     nav.append({package or module.name: modules})

    return nav, abs_api_paths


def _create_page(path: Path, module: Module, filters: list[str]) -> None:
    """Create a page."""
    with path.open("w") as f:
        f.write(module.get_markdown(filters))


def _on_config_plugin(config: MkDocsConfig, plugin: MkAPIPlugin) -> MkDocsConfig:
    # if plugin.config.on_config:
    #     on_config = get_object(plugin.config.on_config)
    #     kwargs, params = {}, inspect.signature(on_config).parameters
    #     if "config" in params:
    #         kwargs["config"] = config
    #     if "plugin" in params:
    #         kwargs["plugin"] = plugin
    #     msg = f"[MkAPI] Calling user 'on_config' with {list(kwargs)}"
    #     logger.info(msg)
    #     config_ = on_config(**kwargs)
    #     if isinstance(config_, MkDocsConfig):
    #         return config_
    return config


# def create_source_page(path: Path, module: Module, filters: list[str]) -> None:
#     """Create a page for source."""
#     filters_str = "|".join(filters)
#     with path.open("w") as f:
#         f.write(f"# ![mkapi]({module.object.id}|code|{filters_str})")


# def clear_prefix(
#     toc: TableOfContents | list[AnchorLink],
#     level: int,
#     id_: str = "",
# ) -> None:
#     """Clear prefix."""
#     for toc_item in toc:
#         if toc_item.level >= level and (not id_ or toc_item.title == id_):
#             toc_item.title = toc_item.title.split(".")[-1]
#         clear_prefix(toc_item.children, level)


# def clean_page_title(page: MkDocsPage) -> None:
#     """Clean page title."""
#     title = str(page.title)
#     if title.startswith("![mkapi]("):
#         page.title = title[9:-1].split("|")[0]  # type: ignore


# def _rmtree(path: Path) -> None:
#     """Delete directory created by MkAPI."""
#     if not path.exists():
#         return
#     try:
#         shutil.rmtree(path)
#     except PermissionError:
#         msg = f"[MkAPI] Couldn't delete directory: {path}"
#         logger.warning(msg)
