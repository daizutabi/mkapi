from __future__ import annotations

import fnmatch
import time
from pathlib import Path
from typing import TYPE_CHECKING

from astdoc.markdown import set_example_class
from astdoc.utils import cache_clear, get_module_path, is_package
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import File, InclusionLevel

import mkapi
import mkapi.nav
import mkapi.renderer
from mkapi.config import Config, get_config, get_function, set_config
from mkapi.page import Page

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page as MkDocsPage
    from mkdocs.structure.toc import AnchorLink, TableOfContents


logger = get_plugin_logger("mkapi")


class Plugin(BasePlugin[Config]):
    pages: dict[str, Page]
    elapsed_time: float

    def __init__(self) -> None:
        self.pages = {}
        set_example_class("mkapi-example-input", "mkapi-example-output")

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        self.elapsed_time = 0
        cache_clear()
        set_config(self.config)

        if before_on_config := get_function("before_on_config"):
            before_on_config(config, self)

        mkapi.renderer.load_templates()

        _update_extensions(config)

        _build_apinav(config)
        self.elapsed_time += _update_nav(config, self.pages)

        if after_on_config := get_function("after_on_config"):
            after_on_config(config, self)

        return config

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs) -> Files:
        start_time = time.perf_counter()

        for src_uri, page in self.pages.items():
            if page.is_api_page():
                if src_uri in files.src_uris:
                    files.remove(files.src_uris[src_uri])
                se = self.config.search_exclude
                if not se:
                    se = page.is_source_page() and self.config.source_search_exclude
                file = generate_file(config, src_uri, page.name, search_exclude=se)
                files.append(file)
                if file.is_modified():
                    msg = f"Generating markdown for {src_uri!r}..."
                    logger.debug(msg)
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

        elapsed_time = time.perf_counter() - start_time
        self.elapsed_time += elapsed_time

        msg = f"{len(self.pages)} pages prepared in {elapsed_time:.2f} seconds"
        logger.info(msg)

        return files

    def on_page_markdown(
        self,
        markdown: str,
        page: MkDocsPage,
        config: MkDocsConfig,
        **kwargs,
    ) -> str:
        start_time = time.perf_counter()
        src_uri = page.file.src_uri

        msg = f"Converting markdown for {src_uri!r}..."
        logger.debug(msg)

        try:
            markdown = self.pages[src_uri].convert_markdown(markdown)
        except Exception as e:
            if self.config.debug:
                raise

            msg = f"{src_uri}:{type(e).__name__}: {e}"
            logger.warning(msg)

        elapsed_time = time.perf_counter() - start_time
        self.elapsed_time += elapsed_time

        if elapsed_time > 0.1:
            msg = f"Converted markdown for {src_uri!r} in {elapsed_time:.2f} seconds"
            logger.debug(msg)

        if self.config.save and self.pages[src_uri].is_api_page():
            path = Path(config.docs_dir) / src_uri
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown, encoding="utf-8")

        return markdown

    def on_page_content(self, html: str, page: MkDocsPage, *args, **kwargs) -> str:
        start_time = time.perf_counter()

        src_uri = page.file.src_uri
        page_ = self.pages[src_uri]

        if page_.is_api_page():
            _replace_toc(page.toc)

        html = page_.convert_html(html)

        self.elapsed_time += time.perf_counter() - start_time
        return html

    def on_post_build(self, *args, **kwargs) -> None:
        msg = f"{len(self.pages)} pages built in {self.elapsed_time:.2f} seconds"
        logger.info(msg)


def _update_extensions(config: MkDocsConfig) -> None:
    for name in ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]:
        if name not in config.markdown_extensions:
            config.markdown_extensions.append(name)


def _build_apinav(config: MkDocsConfig) -> None:
    if not config.nav:
        return

    def watch_directory(name: str, *args) -> list:
        name, depth = mkapi.nav.split_name_depth(name)
        if path := get_module_path(name):
            path = str(path.parent if depth else path)
            if path not in config.watch:
                config.watch.append(path)

        return []

    mkapi.nav.build_apinav(config.nav, watch_directory)


def _update_nav(config: MkDocsConfig, pages: dict[str, Page]) -> float:
    if not (nav := config.nav):
        return 0

    def predicate(name: str) -> bool:
        if name.split(".")[-1].startswith("_"):
            return False

        if not (exclude := get_config().exclude):
            return True

        return not any(fnmatch.fnmatch(name, ex) for ex in exclude)

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
            msg = f"Registered {object_uri!r} for {name!r}"
            logger.debug(msg)

        source_uri = f"{source_path}/{uri}.md"
        if source_uri not in pages:
            pages[source_uri] = Page.create_source(source_uri, name)
            msg = f"Registered {source_uri!r} for {name!r}"
            logger.debug(msg)

        return object_uri

    page_title = get_function("page_title")
    section_title = get_function("section_title")

    exclude = get_config().exclude
    msg = f"Collecting API pages with {len(exclude or [])} exclusion patterns..."
    logger.info(msg)

    start_time = time.perf_counter()
    mkapi.nav.update_nav(nav, create_page, section_title, page_title, predicate)
    elapsed_time = time.perf_counter() - start_time

    msg = f"Navigation updated with {len(pages)} API pages"
    if elapsed_time > 0.1:
        msg += f" in {elapsed_time:.2f} seconds"
    logger.info(msg)

    return elapsed_time


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
    fa = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css"
    config.extra_css = [*uris, *config.extra_css, fa]
    return [File.generated(config, uri, content=_read(uri)) for uri in uris]


def _collect_javascript(config: MkDocsConfig) -> list[File]:
    uris = ["javascript/mkapi.js"]
    config.extra_javascript = [*uris, *config.extra_javascript]
    return [File.generated(config, uri, content=_read(uri)) for uri in uris]


def generate_file(
    config: MkDocsConfig,
    src_uri: str,
    name: str,
    search_exclude: bool = False,
) -> File:
    """Generate a `File` instance for a given source URI and object name.

    Create a `File` instance representing a generated file with the specified
    source URI and object name. The `is_modified` method is set to check if the
    destination file exists and if it is older than the module path.
    This is used to determine if the file needs to be rebuilt in dirty mode.

    Args:
        config (MkDocsConfig): The MkDocs configuration object.
        src_uri (str): The source URI of the file.
        name (str): The object name corresponding to the `src_uri`.
        search_exclude (bool): Whether to exclude the file from search.

    Returns:
        File: A `File` instance representing the generated file.

    """
    if search_exclude:
        content = f"---\nsearch:\n  exclude: true\n---\n\n{name}"
    else:
        content = name

    file = File.generated(config, src_uri, content=content)

    def is_modified() -> bool:
        dest_path = Path(file.abs_dest_path)
        if not dest_path.exists():
            return True

        if not (module_path := get_module_path(name)):
            return True

        return dest_path.stat().st_mtime < module_path.stat().st_mtime

    file.is_modified = is_modified
    return file
