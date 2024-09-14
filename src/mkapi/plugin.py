from __future__ import annotations

import fnmatch
import importlib
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.config import Config, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import File, InclusionLevel, get_files
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

import mkapi
import mkapi.nav
from mkapi import renderer
from mkapi.page import Page
from mkapi.utils import cache_clear, get_module_path, is_package

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page as MkDocsPage
    from mkdocs.structure.toc import AnchorLink, TableOfContents


logger = get_plugin_logger("MkAPI")


class MkApiConfig(Config):
    config = config_options.Type(str, default="")
    exclude = config_options.Type(list, default=[])
    src_dir = config_options.Type(str, default="src")
    docs_anchor = config_options.Type(str, default="docs")
    src_anchor = config_options.Type(str, default="source")
    debug = config_options.Type(bool, default=False)


class MkApiPlugin(BasePlugin[MkApiConfig]):
    pages: dict[str, Page]

    def __init__(self) -> None:
        self.pages = {}
        self.progress = None
        self.task_id = None

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        cache_clear()

        self.page_title = _get_function("page_title", self)
        self.section_title = _get_function("section_title", self)
        self.toc_title = _get_function("toc_title", self)

        if before_on_config := _get_function("before_on_config", self):
            before_on_config(config, self)

        _update_templates(config, self)
        _build_apinav(config, self)
        _update_nav(config, self)
        _update_extensions(config, self)

        if after_on_config := _get_function("after_on_config", self):
            after_on_config(config, self)

        return config

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs) -> Files:
        for src_uri, page in self.pages.items():
            if page.is_api_page() and src_uri not in files.src_uris:
                file = generate_file(config, src_uri, page.name)
                files.append(file)
                if file.is_modified():
                    page.generate_markdown()

        for file in files:
            if page := self.pages.get(file.src_uri):
                if page.is_source_page():
                    file.inclusion = InclusionLevel.NOT_IN_NAV

            elif file.is_documentation_page():
                content = file.content_string
                src_uri = file.src_uri
                self.pages[src_uri] = Page.create_documentation(src_uri, content)

        for file in _collect_css(config, self):
            files.append(file)

        for file in _collect_javascript(config, self):
            files.append(file)

        return files

    def on_nav(self, *args, **kwargs) -> None:
        columns = [
            SpinnerColumn(),
            TextColumn("MkAPI: Building pages"),
            MofNCompleteColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
        ]
        self.progress = Progress(*columns, transient=True)
        self.task_id = self.progress.add_task("", total=len(self.pages))
        self.progress.start()

    def on_page_markdown(self, markdown: str, page: MkDocsPage, **kwargs) -> str:
        src_uri = page.file.src_uri
        page_ = self.pages[src_uri]

        anchors = {"object": self.config.docs_anchor, "source": self.config.src_anchor}

        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=src_uri)

        try:
            return page_.convert_markdown(markdown, anchors)
        except Exception as e:
            if self.config.debug:
                raise

            msg = f"{src_uri}:{type(e).__name__}: {e}"
            logger.warning(msg)
            return markdown

    def on_page_content(
        self, html: str, page: MkDocsPage, config: MkDocsConfig, **kwargs
    ) -> str:
        src_uri = page.file.src_uri
        page_ = self.pages[src_uri]

        if page_.is_api_page():
            _replace_toc(page.toc, self.toc_title)

        anchors = {"object": self.config.docs_anchor, "source": self.config.src_anchor}

        html = page_.convert_html(html, anchors)

        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=src_uri, advance=1)

        return html

    def on_post_build(self, config: MkDocsConfig, **kwargs) -> None:
        if self.progress is not None:
            self.progress.stop()


def _get_function(name: str, plugin: MkApiPlugin) -> Callable | None:
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


def _update_templates(config: MkDocsConfig, plugin: MkApiPlugin) -> None:
    renderer.load_templates()


def _update_extensions(config: MkDocsConfig, plugin: MkApiPlugin) -> None:
    for name in ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]:
        if name not in config.markdown_extensions:
            config.markdown_extensions.append(name)


def _build_apinav(config: MkDocsConfig, plugin: MkApiPlugin) -> None:
    if not config.nav:
        return

    def watch_directory(name: str, *arg):
        name, depth = mkapi.nav.split_name_depth(name)
        if path := get_module_path(name):
            path = str(path.parent if depth else path)
            if path not in config.watch:
                config.watch.append(path)

        return []

    mkapi.nav.build_apinav(config.nav, watch_directory)


def _update_nav(config: MkDocsConfig, plugin: MkApiPlugin) -> None:
    if not (nav := config.nav):
        return

    section_title = plugin.section_title
    page_title = plugin.page_title

    def predicate(name: str) -> bool:
        if name.split(".")[-1].startswith("_"):
            return False

        if not plugin.config.exclude:
            return True

        return not any(fnmatch.fnmatch(name, ex) for ex in plugin.config.exclude)

    columns = [
        SpinnerColumn(),
        TextColumn("MkAPI: Collecting modules"),
        MofNCompleteColumn(),
        BarColumn(),
        TextColumn("{task.description}"),
    ]
    with Progress(*columns, transient=True) as progress:
        task_id = progress.add_task("", total=len(plugin.pages) or None)

        def create_page(name: str, path: str) -> str:
            uri = name.replace(".", "/")

            if ":" in path:
                object_path, source_path = path.split(":", maxsplit=1)
            else:
                object_path, source_path = path, plugin.config.src_dir

            suffix = "/README.md" if is_package(name) else ".md"
            object_uri = f"{object_path}/{uri}{suffix}"
            if object_uri not in plugin.pages:
                plugin.pages[object_uri] = Page.create_object(object_uri, name)
            progress.update(task_id, description=object_uri, advance=1)

            source_uri = f"{source_path}/{uri}.md"
            if source_uri not in plugin.pages:
                plugin.pages[source_uri] = Page.create_source(source_uri, name)
            progress.update(task_id, description=source_uri, advance=1)

            return object_uri

        mkapi.nav.update_nav(nav, create_page, section_title, page_title, predicate)


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


def _collect_css(config: MkDocsConfig, plugin: MkApiPlugin) -> list[File]:
    root = Path(mkapi.__file__).parent / "css"

    if not root.exists():
        return []

    docs_dir = config.docs_dir
    config.docs_dir = root.as_posix()

    theme_name = config.theme.name or "mkdocs"

    files = []
    css = []
    for file in get_files(config):
        if file.src_uri == "mkapi-common.css":
            files.insert(0, file)
            css.insert(0, file.src_uri)

        elif file.src_uri == f"mkapi-{theme_name}.css":
            files.append(file)
            css.append(file.src_uri)

    config.extra_css = [*css, *config.extra_css]
    config.docs_dir = docs_dir
    return files


def _collect_javascript(config: MkDocsConfig, plugin: MkApiPlugin) -> list[File]:
    root = Path(mkapi.__file__).parent / "javascript"

    if not root.exists():
        return []

    docs_dir = config.docs_dir
    config.docs_dir = root.as_posix()

    files = []
    for file in get_files(config):
        files.append(file)
        config.extra_javascript.append(file.src_uri)

    config.docs_dir = docs_dir
    return files


def generate_file(config: MkDocsConfig, src_uri: str, name: str) -> File:
    """Generate a `File` instance for a given source URI and object name.

    Create a `File` instance representing a generated file with the specified
    source URI and object name. The `is_modified` method is set to check if the
    destination file exists and if it is older than the module path.
    This is used to determine if the file needs to be rebuilt in dirty mode.

    Args:
        config (MkDocsConfig): The MkDocs configuration object.
        src_uri (str): The source URI of the file.
        name (str): The object name corresponding to the `src_uri`.

    Returns:
        File: A `File` instance representing the generated file.
    """
    file = File.generated(config, src_uri, content=name)

    def is_modified() -> bool:
        dest_path = Path(file.abs_dest_path)
        if not dest_path.exists():
            return True

        if not (module_path := get_module_path(name)):
            return True

        return dest_path.stat().st_mtime < module_path.stat().st_mtime

    file.is_modified = is_modified
    return file
