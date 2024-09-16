from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import File, InclusionLevel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

import mkapi
import mkapi.nav
import mkapi.renderer
from mkapi.config import MkApiConfig, get_config, get_function, set_config
from mkapi.page import Page
from mkapi.utils import cache_clear, get_module_path, is_package

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page as MkDocsPage
    from mkdocs.structure.toc import AnchorLink, TableOfContents


logger = get_plugin_logger("MkAPI")


class MkApiPlugin(BasePlugin[MkApiConfig]):
    pages: dict[str, Page]

    def __init__(self) -> None:
        self.pages = {}
        self.progress = None
        self.task_id = None

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        cache_clear()
        set_config(self.config)

        if before_on_config := get_function("before_on_config"):
            before_on_config(config, self)

        mkapi.renderer.load_templates()

        _update_extensions(config)

        _build_apinav(config)
        _update_nav(config, self.pages)

        if after_on_config := get_function("after_on_config"):
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

        for file in _collect_css(config):
            files.append(file)

        for file in _collect_javascript(config):
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

        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=src_uri)

        try:
            return self.pages[src_uri].convert_markdown(markdown)
        except Exception as e:
            if self.config.debug:
                raise

            msg = f"{src_uri}:{type(e).__name__}: {e}"
            logger.warning(msg)
            return markdown

    def on_page_content(self, html: str, page: MkDocsPage, *args, **kwargs) -> str:
        src_uri = page.file.src_uri
        page_ = self.pages[src_uri]

        if page_.is_api_page():
            _replace_toc(page.toc)

        html = page_.convert_html(html)

        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=src_uri, advance=1)

        return html

    def on_post_build(self, *args, **kwargs) -> None:
        if self.progress is not None:
            self.progress.stop()


def _update_extensions(config: MkDocsConfig) -> None:
    for name in ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]:
        if name not in config.markdown_extensions:
            config.markdown_extensions.append(name)


def _build_apinav(config: MkDocsConfig) -> None:
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


def _update_nav(config: MkDocsConfig, pages: dict[str, Page]) -> None:
    if not (nav := config.nav):
        return

    def predicate(name: str) -> bool:
        if name.split(".")[-1].startswith("_"):
            return False

        if not (exclude := get_config().exclude):
            return True

        return not any(fnmatch.fnmatch(name, ex) for ex in exclude)

    columns = [
        SpinnerColumn(),
        TextColumn("MkAPI: Collecting modules"),
        MofNCompleteColumn(),
        BarColumn(),
        TextColumn("{task.description}"),
    ]
    with Progress(*columns, transient=True) as progress:
        task_id = progress.add_task("", total=len(pages) or None)

        def create_page(name: str, path: str) -> str:
            uri = name.replace(".", "/")

            if ":" in path:
                object_path, source_path = path.split(":", maxsplit=1)
            else:
                object_path, source_path = path, "src"

            suffix = "/README.md" if is_package(name) else ".md"
            object_uri = f"{object_path}/{uri}{suffix}"
            if object_uri not in pages:
                pages[object_uri] = Page.create_object(object_uri, name)

            progress.update(task_id, description=object_uri, advance=1)

            source_uri = f"{source_path}/{uri}.md"
            if source_uri not in pages:
                pages[source_uri] = Page.create_source(source_uri, name)

            progress.update(task_id, description=source_uri, advance=1)

            return object_uri

        page_title = get_function("page_title")
        section_title = get_function("section_title")

        mkapi.nav.update_nav(nav, create_page, section_title, page_title, predicate)


def _replace_toc(toc: TableOfContents | list[AnchorLink], depth: int = 0) -> None:
    toc_title = get_function("toc_title")

    for link in toc:
        if toc_title:
            link.title = toc_title(link.title, depth)
        else:
            link.title = link.title.split(".")[-1]

        _replace_toc(link.children, depth + 1)


def _read(uri: str) -> str:
    root = Path(mkapi.__file__).parent
    return (root / uri).read_text()


def _collect_css(config: MkDocsConfig) -> list[File]:
    uris = ["css/mkapi-common.css", "css/mkapi-material.css"]
    config.extra_css = [*uris, *config.extra_css]
    return [File.generated(config, uri, content=_read(uri)) for uri in uris]


def _collect_javascript(config: MkDocsConfig) -> list[File]:
    uris = ["javascript/mkapi.js"]
    config.extra_javascript = [*uris, *config.extra_javascript]
    return [File.generated(config, uri, content=_read(uri)) for uri in uris]


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
