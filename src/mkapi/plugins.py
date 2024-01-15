"""MkAPI Plugin class.

MkAPI Plugin is a MkDocs plugin that creates Python API documentation
from Docstring.
"""
from __future__ import annotations

import importlib
import logging
import os
import re
import sys
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, TypeGuard

import yaml
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files, get_files

import mkapi
from mkapi import renderers
from mkapi.pages import collect_objects
from mkapi.utils import find_submodulenames, is_package, split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.structure.pages import Page as MkDocsPage
    from mkdocs.structure.toc import AnchorLink, TableOfContents
    # from mkdocs.utils.templates import TemplateContext
    # from mkdocs.structure.nav import Navigation

from mkapi.pages import Page as MkAPIPage

logger = logging.getLogger("mkdocs")


class MkAPIConfig(Config):
    """Specify the config schema."""

    src_dirs = config_options.Type(list, default=[])
    filters = config_options.Type(list, default=[])
    exclude = config_options.Type(list, default=[])
    page_title = config_options.Type(str, default="")
    section_title = config_options.Type(str, default="")
    on_config = config_options.Type(str, default="")
    pages = config_options.Type(dict, default={})


class MkAPIPlugin(BasePlugin[MkAPIConfig]):
    """MkAPIPlugin class for API generation."""

    nav = None

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        _insert_sys_path(self.config)
        _update_templates(config, self)
        _update_config(config, self)
        if "admonition" not in config.markdown_extensions:
            config.markdown_extensions.append("admonition")
        return _on_config_plugin(config, self)

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs) -> Files:
        """Collect plugin CSS/JavaScript and append them to `files`."""
        root = Path(mkapi.__file__).parent / "themes"
        docs_dir = config.docs_dir
        config.docs_dir = root.as_posix()
        theme_files = get_files(config)
        config.docs_dir = docs_dir
        theme_name = config.theme.name or "mkdocs"

        css = []
        js = []
        for file in theme_files:
            path = Path(file.src_path).as_posix()
            if path.endswith(".css"):
                if "common" in path or theme_name in path:
                    files.append(file)
                    css.append(path)
            elif path.endswith(".js"):
                files.append(file)
                js.append(path)
            elif path.endswith(".yml"):
                with (root / path).open() as f:
                    data = yaml.safe_load(f)
                css = data.get("extra_css", []) + css
                js = data.get("extra_javascript", []) + js
        css = [x for x in css if x not in config.extra_css]
        js = [x for x in js if x not in config.extra_javascript]
        config.extra_css.extend(css)
        config.extra_javascript.extend(js)

        return files

    def on_page_markdown(self, markdown: str, page: MkDocsPage, **kwargs) -> str:
        """Convert Markdown source to intermediate version."""
        # clean_page_title(page)
        abs_src_path = page.file.abs_src_path
        mkapi_page = MkAPIPage(markdown, abs_src_path, self.config.filters)
        self.config.pages[abs_src_path] = mkapi_page
        return mkapi_page.convert_markdown()

    def on_page_content(self, html: str, page: MkDocsPage, **kwargs) -> str:
        """Merge HTML and MkAPI's object structure."""
        # if page.title:
        #     page.title = re.sub(r"<.*?>", "", str(page.title))  # type: ignore
        mkapi_page: MkAPIPage = self.config.pages[page.file.abs_src_path]
        return mkapi_page.convert_html(html)

    # def on_page_context(
    #     self,
    #     context: TemplateContext,
    #     page: MkDocsPage,
    #     config: MkDocsConfig,
    #     nav: Navigation,
    #     **kwargs,
    # ) -> TemplateContext:
    #     """Clear prefix in toc."""
    #     src_uri = page.file.src_uri
    #     if src_uri in self.config.pages:
    #         pass
    #         # clear_prefix(page.toc, 2)
    #     else:
    #         mkapi_page: MkAPIPage = self.config.pages[abs_src_path]
    #         # for level, id_ in mkapi_page.headings:
    #         #     clear_prefix(page.toc, level, id_)
    #     return context

    def on_serve(self, server, config: MkDocsConfig, builder, **kwargs):
        for path in ["themes", "templates"]:
            path_str = (Path(mkapi.__file__).parent / path).as_posix()
            server.watch(path_str, builder)
        return server


def _on_config_plugin(config: MkDocsConfig, plugin: MkAPIPlugin) -> MkDocsConfig:
    if func := _get_function(plugin, "on_config"):
        msg = f"[MkAPI] Calling user 'on_config': {plugin.config.on_config}"
        logger.info(msg)
        config_ = func(config, plugin)
        if isinstance(config_, MkDocsConfig):
            return config_
    return config


def _insert_sys_path(config: MkAPIConfig) -> None:
    config_dir = Path(config.config_file_path).parent
    for src_dir in config.src_dirs:
        path = os.path.normpath(config_dir / src_dir)
        if path not in sys.path:
            sys.path.insert(0, path)


def _update_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not MkAPIPlugin.nav:
        _update_nav(config, plugin)
        MkAPIPlugin.nav = config.nav
    else:
        config.nav = MkAPIPlugin.nav


def _update_templates(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    renderers.load_templates()


def _update_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    create_pages = partial(_create_pages, config=config, plugin=plugin)
    config.nav = _walk_nav(config.nav, create_pages)  # type: ignore


def _walk_nav(nav: list, create_pages: Callable[[str], list]) -> list:
    nav_ = []
    for item in nav:
        if _is_api_entry(item):
            nav_.extend(create_pages(item))
        elif isinstance(item, dict) and len(item) == 1:
            key = next(iter(item.keys()))
            value = item[key]
            if _is_api_entry(value):
                value = create_pages(value)
                if len(value) == 1 and isinstance(value[0], str):
                    value = value[0]
            elif isinstance(value, list):
                value = _walk_nav(value, create_pages)
            nav_.append({key: value})
        else:
            nav_.append(item)
    return nav_


API_URL_PATTERN = re.compile(r"^\<(.+)\>/(.+)$")


def _is_api_entry(item: str | list | dict) -> TypeGuard[str]:
    if not isinstance(item, str):
        return False
    return re.match(API_URL_PATTERN, item) is not None


def _get_path_modulename_filters(
    item: str,
    filters: list[str],
) -> tuple[str, str, list[str]]:
    if not (m := re.match(API_URL_PATTERN, item)):
        raise NotImplementedError
    path, modulename_filter = m.groups()
    modulename, filters_ = split_filters(modulename_filter)
    filters = update_filters(filters, filters_)
    return path, modulename, filters


def _create_nav(
    name: str,
    callback: Callable[[str, int, bool], str | dict[str, str]],
    section: Callable[[str, int], str | None] | None = None,
    predicate: Callable[[str], bool] | None = None,
    depth: int = 0,
) -> list:
    names = find_submodulenames(name, predicate)
    tree: list = [callback(name, depth, is_package(name))]
    for sub in names:
        if not is_package(sub):
            tree.append(callback(sub, depth, False))  # noqa: FBT003
            continue
        subtree = _create_nav(sub, callback, section, predicate, depth + 1)
        if len(subtree):
            title = section(sub, depth) if section else sub
            tree.append({title: subtree})
    return tree


def _get_function(plugin: MkAPIPlugin, name: str) -> Callable | None:
    if fullname := plugin.config.get(name, None):
        modulename, func_name = fullname.rsplit(".", maxsplit=1)
        module = importlib.import_module(modulename)
        return getattr(module, func_name)
    return None


def _create_pages(item: str, config: MkDocsConfig, plugin: MkAPIPlugin) -> list:
    """Collect modules."""
    api_path, name, filters = _get_path_modulename_filters(item, plugin.config.filters)
    abs_api_path = Path(config.docs_dir) / api_path
    Path.mkdir(abs_api_path, parents=True, exist_ok=True)

    page_title = _get_function(plugin, "page_title")
    section_title = _get_function(plugin, "section_title")
    if plugin.config.exclude:

        def predicate(name: str) -> bool:
            return all(e not in name for e in plugin.config.exclude)
    else:
        predicate = None  # type: ignore

    def callback(name: str, depth: int, ispackage) -> dict[str, str]:
        module_path = name + ".md"
        abs_path = abs_api_path / module_path
        collect_objects(name, abs_path)
        _create_page(name, abs_path, filters)
        src_uri = (Path(api_path) / module_path).as_posix()
        title = page_title(name, depth, ispackage) if page_title else name
        return {title: src_uri}

    return _create_nav(name, callback, section_title, predicate)


def _create_page(name: str, path: Path, filters: list[str]) -> None:
    with path.open("w") as file:
        file.write(renderers.render_module(name, filters))


def _clear_prefix(
    toc: TableOfContents | list[AnchorLink],
    name: str,
    level: int,
) -> None:
    """Clear prefix."""
    for toc_item in toc:
        if toc_item.level >= level and (not name or toc_item.title == name):
            toc_item.title = toc_item.title.split(".")[-1]
        _clear_prefix(toc_item.children, "", level)


def _clean_page_title(page: MkDocsPage) -> None:
    """Clean page title."""
    title = str(page.title)
    if title.startswith("![mkapi]("):
        page.title = title[9:-1].split("|")[0]  # type: ignore


# def _rmtree(path: Path) -> None:
#     """Delete directory created by MkAPI."""
#     if not path.exists():
#         return
#     try:
#         shutil.rmtree(path)
#     except PermissionError:
#         msg = f"[MkAPI] Couldn't delete directory: {path}"
#         logger.warning(msg)

# def create_source_page(path: Path, module: Module, filters: list[str]) -> None:
#     """Create a page for source."""
#     filters_str = "|".join(filters)
#     with path.open("w") as f:
#         f.write(f"# ![mkapi]({module.object.id}|code|{filters_str})")
