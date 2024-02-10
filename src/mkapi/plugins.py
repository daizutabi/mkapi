"""MkAPI Plugin class.

MkAPI Plugin is a MkDocs plugin that creates Python API documentation
from Docstring.
"""
from __future__ import annotations

import importlib
import itertools
import os
import re
import shutil
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from halo import Halo
from mkdocs.config import Config, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import InclusionLevel, get_files
from tqdm.std import tqdm

import mkapi
import mkapi.nav
from mkapi import renderers
from mkapi.importlib import cache_clear
from mkapi.nav import split_name_depth
from mkapi.pages import (
    convert_markdown,
    convert_source,
    create_object_page,
    create_source_page,
)
from mkapi.utils import get_module_path, is_module_cache_dirty

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File, Files
    from mkdocs.structure.pages import Page as MkDocsPage
    from mkdocs.structure.toc import AnchorLink, TableOfContents

logger = get_plugin_logger("MkAPI")


class MkAPIConfig(Config):
    """Specify the config schema."""

    config = config_options.Type(str, default="")
    exclude = config_options.Type(list, default=[])
    filters = config_options.Type(list, default=[])
    src_dir = config_options.Type(str, default="src")
    docs_anchor = config_options.Type(str, default="docs")
    src_anchor = config_options.Type(str, default="source")
    debug = config_options.Type(bool, default=False)


class MkAPIPlugin(BasePlugin[MkAPIConfig]):
    """MkAPIPlugin class for API generation."""

    api_dirs: list[Path]
    api_uris: list[str]
    api_srcs: list[str]

    def __init__(self) -> None:
        self.api_dirs = []

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        self.api_uris = []
        self.api_srcs = []
        if before_on_config := _get_function("before_on_config", self):
            before_on_config(config, self)
        _update_templates(config, self)
        _create_nav(config, self)
        _update_nav(config, self)
        _update_extensions(config, self)
        if after_on_config := _get_function("after_on_config", self):
            after_on_config(config, self)
        return config

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs) -> Files:
        """Collect plugin CSS and append them to `files`."""
        for file in files:
            if file.src_uri.startswith(f"{self.config.src_dir}/"):
                file.inclusion = InclusionLevel.NOT_IN_NAV
        for file in _collect_stylesheets(config, self):
            files.append(file)
        return files

    def on_nav(self, *args, **kwargs) -> None:
        total = len(self.api_uris) + len(self.api_srcs)
        uris = self.api_uris + self.api_srcs
        if uris:
            self.uri_width = max(len(uri) for uri in uris)
            desc = "MkAPI: Building API pages"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.bar = tqdm(desc=desc, total=total, leave=False)
        else:
            self.bar = None

    def on_page_markdown(self, markdown: str, page: MkDocsPage, **kwargs) -> str:
        """Convert Markdown source to intermediate version."""
        path = page.file.abs_src_path
        anchor = self.config.src_anchor
        filters = self.config.filters
        try:
            return convert_markdown(markdown, path, anchor, filters)
        except Exception as e:  # noqa: BLE001
            if self.config.debug:
                raise
            msg = f"{page.file.src_uri}:{type(e).__name__}: {e}"
            logger.warning(msg)
            return markdown

    def on_page_content(
        self,
        html: str,
        page: MkDocsPage,
        config: MkDocsConfig,
        **kwargs,
    ) -> str:
        """Merge HTML and MkAPI's object structure."""
        toc_title = _get_function("toc_title", self)
        if page.file.src_uri in self.api_uris:
            _replace_toc(page.toc, toc_title)
            self._update_bar(page.file.src_uri)
        if page.file.src_uri in self.api_srcs:
            path = Path(config.docs_dir) / page.file.src_uri
            html = convert_source(html, path, self.config.docs_anchor)
            self._update_bar(page.file.src_uri)
        return html

    def _update_bar(self, uri: str) -> None:
        if not self.bar:
            return
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            uri = uri.ljust(self.uri_width)
            self.bar.set_postfix_str(uri, refresh=False)
        self.bar.update(1)
        if self.bar.n == self.bar.total:
            self.bar.close()

    def on_shutdown(self) -> None:
        for path in self.api_dirs:
            if path.exists():
                logger.info(f"Deleting API directory: {path}")
                shutil.rmtree(path)


def _get_function(name: str, plugin: MkAPIPlugin) -> Callable | None:
    if not (path_str := plugin.config.config):
        return None
    if not path_str.endswith(".py"):
        module = importlib.import_module(path_str)
    else:
        path = Path(path_str)
        if not path.is_absolute():
            path = Path(plugin.config.config_file_path).parent / path
        directory = os.path.normpath(path.parent)
        sys.path.insert(0, directory)
        module = importlib.import_module(path.stem)
        del sys.path[0]
    return getattr(module, name, None)


def _update_templates(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:  # noqa: ARG001
    renderers.load_templates()


def _update_extensions(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:  # noqa: ARG001
    for name in ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]:
        if name not in config.markdown_extensions:
            config.markdown_extensions.append(name)


def _watch_directory(name: str, config: MkDocsConfig) -> None:
    if not name:
        return
    name, depth = split_name_depth(name)
    if path := get_module_path(name):
        path = str(path.parent if depth else path)
        if path not in config.watch:
            config.watch.append(path)


def _create_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not config.nav:
        return

    def mkdir(name: str, path: str) -> list:
        # _watch_directory(name, config)
        api_dir = Path(config.docs_dir) / path
        if api_dir.exists() and api_dir not in plugin.api_dirs:
            logger.warning(f"API directory exists: {api_dir}")
            ans = input("Delete the directory? [yes/no] ")
            if ans.lower() == "yes":
                logger.info(f"Deleting API directory: {api_dir}")
                shutil.rmtree(api_dir)
            else:
                logger.error("Delete the directory manually.")
                sys.exit()
        if not api_dir.exists():
            msg = f"Making API directory: {api_dir}"
            logger.info(msg)
            api_dir.mkdir()
            plugin.api_dirs.append(api_dir)
        return []

    mkapi.nav.create(config.nav, lambda *args: mkdir(args[0], args[1]))
    mkdir("", plugin.config.src_dir)


def _check_path(path: Path):
    # if path.exists():
    #     msg = f"Duplicated page: {path.as_posix()!r}"
    #     logger.warning(msg)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)


def _update_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not config.nav:
        return

    page_title = _get_function("page_title", plugin)
    section_title = _get_function("section_title", plugin)

    def _create_page(name: str, path: str, filters: list[str], depth: int) -> str:
        is_dirty = is_module_cache_dirty(name)
        if is_dirty:
            cache_clear()

        n = len(plugin.api_uris)
        spinner.text = f"Collecting modules [{n:>3}]: {name}"

        abs_path = Path(config.docs_dir) / path

        if not abs_path.exists():
            _check_path(abs_path)
            create_object_page(f"{name}.**", abs_path, [*filters, "sourcelink"])
        plugin.api_uris.append(path)

        path = plugin.config.src_dir + "/" + name.replace(".", "/") + ".md"
        abs_path = Path(config.docs_dir) / path

        if not abs_path.exists():
            _check_path(abs_path)
            create_source_page(f"{name}.**", abs_path, filters)
        plugin.api_srcs.append(path)

        return page_title(name, depth) if page_title else name

    def predicate(name: str) -> bool:
        if not plugin.config.exclude:
            return True
        return any(ex not in name for ex in plugin.config.exclude)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spinner = Halo()
        spinner.start()
        mkapi.nav.update(config.nav, _create_page, section_title, predicate)
        spinner.stop()


def _collect_stylesheets(config: MkDocsConfig, plugin: MkAPIPlugin) -> list[File]:  # noqa: ARG001
    root = Path(mkapi.__file__).parent / "stylesheets"
    docs_dir = config.docs_dir
    config.docs_dir = root.as_posix()
    stylesheet_files = get_files(config)
    config.docs_dir = docs_dir
    theme_name = config.theme.name or "mkdocs"
    files: list[File] = []
    css: list[str] = []
    for file in stylesheet_files:
        path = Path(file.src_path).as_posix()
        if path.endswith("mkapi-common.css"):
            files.insert(0, file)
            css.insert(0, path)
        elif path.endswith(f"mkapi-{theme_name}.css"):
            files.append(file)
            css.append(path)
    config.extra_css = [*css, *config.extra_css]
    return files


def _replace_toc(
    toc: TableOfContents | list[AnchorLink],
    title: Callable[[str, int], str] | None = None,
    depth: int = 0,
) -> None:
    for link in toc:
        link.title = re.sub(r"\s+\[.+?\]", "", link.title)  # Remove source link.
        if title:
            link.title = title(link.title, depth)
        else:
            link.title = link.title.split(".")[-1]  # Remove prefix.
        _replace_toc(link.children, title, depth + 1)
