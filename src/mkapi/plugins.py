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
from typing import TYPE_CHECKING, ClassVar

import yaml
from halo import Halo
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import InclusionLevel, get_files
from tqdm.std import tqdm

import mkapi
import mkapi.nav
from mkapi import renderers
from mkapi.pages import (
    convert_markdown,
    convert_source,
    create_object_page,
    create_source_page,
)

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
    debug = config_options.Type(bool, default=False)
    docs_anchor = config_options.Type(str, default="docs")
    exclude = config_options.Type(list, default=[])
    filters = config_options.Type(list, default=[])
    src_anchor = config_options.Type(str, default="source")
    src_dir = config_options.Type(str, default="src")


class MkAPIPlugin(BasePlugin[MkAPIConfig]):
    """MkAPIPlugin class for API generation."""

    nav: ClassVar[list | None] = None
    api_dirs: ClassVar[list] = []
    api_uris: ClassVar[list] = []
    api_srcs: ClassVar[list] = []
    api_uri_width: ClassVar[int] = 0

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        if before_on_config := _get_function("before_on_config", self):
            before_on_config(config, self)
        _update_templates(config, self)
        _update_config(config, self)
        _update_extensions(config, self)
        if after_on_config := _get_function("after_on_config", self):
            after_on_config(config, self)
        return config

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs) -> Files:
        """Collect plugin CSS/JavaScript and append them to `files`."""
        for file in files:
            if file.src_uri.startswith(f"{self.config.src_dir}/"):
                file.inclusion = InclusionLevel.NOT_IN_NAV
        for file in _collect_theme_files(config, self):
            files.append(file)
        return files

    def on_nav(self, *args, **kwargs) -> None:
        total = len(MkAPIPlugin.api_uris) + len(MkAPIPlugin.api_srcs)
        desc = "MkAPI: Building API"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.bar = tqdm(desc=desc, total=total, leave=False)

    def on_page_markdown(self, markdown: str, page: MkDocsPage, **kwargs) -> str:
        """Convert Markdown source to intermediate version."""
        path = page.file.abs_src_path
        filters = self.config.filters
        anchor = self.config.src_anchor
        try:
            return convert_markdown(markdown, path, filters, anchor)
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
        if page.file.src_uri in MkAPIPlugin.api_uris:
            _replace_toc(page.toc, toc_title)
            self._update_bar(page.file.src_uri)
        if page.file.src_uri in MkAPIPlugin.api_srcs:
            path = Path(config.docs_dir) / page.file.src_uri
            html = convert_source(html, path, self.config.docs_anchor)
            self._update_bar(page.file.src_uri)
        return html

    def _update_bar(self, uri: str) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            uri = uri.ljust(MkAPIPlugin.api_uri_width)
            self.bar.set_postfix_str(uri, refresh=False)
        self.bar.update(1)

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        self.bar.close()

    def on_serve(self, server, config: MkDocsConfig, builder, **kwargs):
        if self.config.debug:
            for path in ["themes", "templates"]:
                path_str = (Path(mkapi.__file__).parent / path).as_posix()
                server.watch(path_str, builder)
        return server

    def on_shutdown(self) -> None:
        for path in MkAPIPlugin.api_dirs:
            if path.exists():
                msg = f"Removing API directory: {path}"
                logger.info(msg)
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


def _update_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not MkAPIPlugin.nav:
        _create_nav(config, plugin)
        _update_nav(config, plugin)
        MkAPIPlugin.nav = config.nav
        uris = itertools.chain(MkAPIPlugin.api_uris, MkAPIPlugin.api_srcs)
        MkAPIPlugin.api_uri_width = max(len(uri) for uri in uris)
    else:
        config.nav = MkAPIPlugin.nav


def _update_extensions(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:  # noqa: ARG001
    for name in ["admonition", "attr_list", "md_in_html", "pymdownx.superfences"]:
        if name not in config.markdown_extensions:
            config.markdown_extensions.append(name)


def _create_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not config.nav:
        return

    def mkdir(path: str) -> list:
        api_dir = Path(config.docs_dir) / path
        if api_dir.exists() and api_dir not in MkAPIPlugin.api_dirs:
            msg = f"API directory exists: {api_dir}"
            logger.error(msg)
            sys.exit()
        if not api_dir.exists():
            msg = f"Making API directory: {api_dir}"
            logger.info(msg)
            api_dir.mkdir()
            MkAPIPlugin.api_dirs.append(api_dir)
        return []

    mkapi.nav.create(config.nav, lambda *args: mkdir(args[1]))
    mkdir(plugin.config.src_dir)


def _check_path(path: Path):
    if path.exists():
        msg = f"Duplicated page: {path.as_posix()!r}"
        logger.warning(msg)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)


def _update_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not config.nav:
        return

    page_title = _get_function("page_title", plugin)
    section_title = _get_function("section_title", plugin)

    def _create_page(name: str, path: str, filters: list[str], depth: int) -> str:
        spinner.text = f"Updating nav...: {name}"
        MkAPIPlugin.api_uris.append(path)
        abs_path = Path(config.docs_dir) / path
        _check_path(abs_path)
        create_object_page(f"{name}.**", abs_path, [*filters, "sourcelink"])

        path = plugin.config.src_dir + "/" + name.replace(".", "/") + ".md"
        MkAPIPlugin.api_srcs.append(path)
        abs_path = Path(config.docs_dir) / path
        _check_path(abs_path)
        create_source_page(f"{name}.**", abs_path, filters)

        return page_title(name, depth) if page_title else name

    def predicate(name: str) -> bool:
        return any(ex not in name for ex in plugin.config.exclude)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spinner = Halo()
        spinner.start()
        mkapi.nav.update(config.nav, _create_page, section_title, predicate)
        spinner.stop()


def _collect_theme_files(config: MkDocsConfig, plugin: MkAPIPlugin) -> list[File]:  # noqa: ARG001
    root = Path(mkapi.__file__).parent / "themes"
    docs_dir = config.docs_dir
    config.docs_dir = root.as_posix()
    theme_files = get_files(config)
    config.docs_dir = docs_dir
    theme_name = config.theme.name or "mkdocs"
    files: list[File] = []
    css: list[str] = []
    js: list[str] = []
    for file in theme_files:
        path = Path(file.src_path).as_posix()
        if path.endswith(".css"):
            if "common" in path or theme_name in path:
                files.append(file)
                css.append(path)
        elif path.endswith(".js"):
            files.append(file)
            js.append(path)
        elif path.endswith((".yml", ".yaml")):
            with (root / path).open() as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                css.extend(data.get("extra_css", []))
                js.extend(data.get("extra_javascript", []))
    css = [f for f in css if f not in config.extra_css]
    js = [f for f in js if f not in config.extra_javascript]
    config.extra_css.extend(css)
    config.extra_javascript.extend(js)
    return files


def _replace_toc(
    toc: TableOfContents | list[AnchorLink],
    title: Callable[[str, int], str] | None = None,
    depth: int = 0,
) -> None:
    for link in toc:
        # link.id = link.id.replace("\0295\03", "_")
        link.title = re.sub(r"\s+\[.+?\]", "", link.title)  # Remove source link.
        if title:
            link.title = title(link.title, depth)
        else:
            link.title = link.title.split(".")[-1]  # Remove prefix.
        _replace_toc(link.children, title, depth + 1)
