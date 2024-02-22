"""MkAPI Plugin class.

MkAPI Plugin is a MkDocs plugin that creates Python API documentation
from Docstring.
"""
from __future__ import annotations

import importlib
import os
import re
import shutil
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from halo import Halo
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import File, InclusionLevel, get_files
from tqdm.std import tqdm

import mkapi
import mkapi.nav

# from mkapi import renderers
from mkapi.nav import split_name_depth

# from mkapi.pages import Page, PageKind
from mkapi.utils import (
    cache_clear,
    get_module_path,
    is_module_cache_dirty,
    is_package,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.livereload import LiveReloadServer
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page as MkDocsPage
    from mkdocs.structure.toc import AnchorLink, TableOfContents
    # from mkdocs.structure.nav import Navigation
    # from mkdocs.utils.templates import TemplateContext

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
    pages: dict[str, Page]

    def __init__(self) -> None:
        self.api_dirs = []
        self.pages = {}
        self.server = None
        self.dirty = False

    def on_startup(self, *, command: str, dirty: bool) -> None:
        self.dirty = dirty

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        cache_clear()

        if self.dirty:
            pages: list[Page] = []
            for page in self.pages.values():
                if page.name and is_module_cache_dirty(page.name):
                    pages.append(page)  # noqa: PERF401
            for page in pages:
                page.create_markdown()

        self.bar = None
        self.uri_width = 0

        self.page_title = _get_function("page_title", self)
        self.section_title = _get_function("section_title", self)
        self.toc_title = _get_function("toc_title", self)

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
            if page := self.pages.get(file.src_uri):
                if page.kind is PageKind.SOURCE:
                    file.inclusion = InclusionLevel.NOT_IN_NAV

            elif file.is_documentation_page():
                path = Path(file.abs_src_path)
                self.pages[file.src_uri] = Page("", path, PageKind.MARKDOWN, [])

        for file in _collect_stylesheets(config, self):
            files.append(file)

        return files

    def on_nav(self, *args, **kwargs) -> None:
        if self.pages and not (self.dirty and self.server):
            self.uri_width = max(len(uri) for uri in self.pages)
            desc = "MkAPI: Building API pages"

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.bar = tqdm(desc=desc, total=len(self.pages), leave=False)

    def on_page_markdown(self, markdown: str, page: MkDocsPage, **kwargs) -> str:
        """Convert Markdown source to intermediate version."""
        uri = page.file.src_uri
        page_ = self.pages[uri]

        anchors = {"object": self.config.docs_anchor, "source": self.config.src_anchor}

        try:
            return page_.convert_markdown(markdown, anchors)
        except Exception as e:  # noqa: BLE001
            if self.config.debug:
                raise

            msg = f"{uri}:{type(e).__name__}: {e}"
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
        uri = page.file.src_uri
        page_ = self.pages[uri]

        if page_.kind in [PageKind.OBJECT, PageKind.SOURCE]:
            _replace_toc(page.toc, self.toc_title)

        anchors = {"object": self.config.docs_anchor, "source": self.config.src_anchor}

        html = page_.convert_html(html, anchors)

        self._update_bar(page.file.src_uri)
        return html

    def _update_bar(self, uri: str) -> None:
        if not self.bar:
            return

        uri = uri.ljust(self.uri_width)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.bar.set_postfix_str(uri, refresh=False)

        self.bar.update(1)
        if self.bar.n == self.bar.total:
            self.bar.close()

    # def on_page_context(
    #     self,
    #     context: TemplateContext,
    #     *,
    #     page: MkDocsPage,
    #     config: MkDocsConfig,
    #     nav: Navigation,
    # ) -> TemplateContext | None:
    #     if len(nav.items):
    #         nav.items.pop()
    #     return context

    def on_serve(self, server: LiveReloadServer, *args, **kwargs) -> None:
        self.server = server

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


def _mkdir(path: Path, paths: list[Path]) -> None:
    if path.exists() and path not in paths:
        logger.warning(f"API directory exists: {path}")

        ans = input("Delete the directory? [yes/no] ")
        if ans.lower() == "yes":
            logger.info(f"Deleting API directory: {path}")
            shutil.rmtree(path)
        else:
            logger.error("Delete the directory manually.")
            sys.exit()

    if not path.exists():
        msg = f"Making API directory: {path}"

        logger.info(msg)
        path.mkdir(parents=True)
        paths.append(path)


def _split_path(path: str, plugin: MkAPIPlugin) -> list[str]:
    if ":" in path:
        return path.split(":", maxsplit=1)
    return [path, plugin.config.src_dir]


def _create_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not config.nav:
        return

    def mkdir(name: str, path: str) -> list:
        _watch_directory(name, config)

        for path_ in _split_path(path, plugin):
            api_dir = Path(config.docs_dir) / path_
            _mkdir(api_dir, plugin.api_dirs)

        return []

    mkapi.nav.create(config.nav, lambda *args: mkdir(args[0], args[1]))


def _update_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not config.nav:
        return

    def _create_page(name: str, path: str, filters: list[str]) -> str:
        uri = name.replace(".", "/")
        object_path, source_path = _split_path(path, plugin)

        suffix = "/README.md" if is_package(name) else ".md"
        object_uri = f"{object_path}/{uri}{suffix}"
        abs_path = Path(config.docs_dir) / object_uri

        if object_uri not in plugin.pages:
            plugin.pages[object_uri] = Page(name, abs_path, PageKind.OBJECT, filters)

        source_uri = f"{source_path}/{uri}.md"
        abs_path = Path(config.docs_dir) / source_uri

        if source_uri not in plugin.pages:
            plugin.pages[source_uri] = Page(name, abs_path, PageKind.SOURCE, filters)

        spinner.text = f"Collecting modules [{len(plugin.pages):>3}]: {name}"

        return object_uri

    def predicate(name: str) -> bool:
        if not plugin.config.exclude:
            return True
        return all(ex not in name for ex in plugin.config.exclude)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        spinner = Halo()
        spinner.start()

        try:
            mkapi.nav.update(
                config.nav,
                _create_page,
                plugin.section_title,
                plugin.page_title,
                predicate,
            )
        except Exception as e:
            if plugin.config.debug:
                raise

            spinner.stop()
            logger.exception(e)  # noqa: TRY401
        else:
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
