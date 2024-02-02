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
from typing import TYPE_CHECKING, ClassVar

import yaml
from halo import Halo
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import Files, InclusionLevel, get_files
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

    docs_anchor = config_options.Type(str, default="docs")
    exclude = config_options.Type(list, default=[])
    filters = config_options.Type(list, default=[])
    page_title = config_options.Type(str, default="")
    section_title = config_options.Type(str, default="")
    src_anchor = config_options.Type(str, default="source")
    src_dir = config_options.Type(str, default="src")
    # on_config = config_options.Type(str, default="")


class MkAPIPlugin(BasePlugin[MkAPIConfig]):
    """MkAPIPlugin class for API generation."""

    nav: ClassVar[list | None] = None
    api_dirs: ClassVar[list] = []
    api_uris: ClassVar[list] = []
    api_srcs: ClassVar[list] = []

    def on_config(self, config: MkDocsConfig, **kwargs) -> MkDocsConfig:
        _insert_sys_path(config, self)
        _update_templates(config, self)
        _update_config(config, self)
        _update_extensions(config, self)
        return config
        # return _on_config_plugin(config, self)

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
        return convert_markdown(markdown, path, filters, self.config.src_anchor)

    def on_page_content(
        self,
        html: str,
        page: MkDocsPage,
        config: MkDocsConfig,
        **kwargs,
    ) -> str:
        """Merge HTML and MkAPI's object structure."""
        if page.file.src_uri in MkAPIPlugin.api_uris:
            _replace_toc(page.toc)
            self.bar.update(1)
        if page.file.src_uri in MkAPIPlugin.api_srcs:
            path = Path(config.docs_dir) / page.file.src_uri
            html = convert_source(html, path, self.config.docs_anchor)
            self.bar.update(1)
        return html

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        self.bar.close()

    def on_serve(self, server, config: MkDocsConfig, builder, **kwargs):
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
    if fullname := plugin.config.get(name, None):
        module_name, func_name = fullname.rsplit(".", maxsplit=1)
        module = importlib.import_module(module_name)
        return getattr(module, func_name)
    return None


def _insert_sys_path(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    config_dir = Path(config.config_file_path).parent
    path = os.path.normpath(config_dir)
    if path not in sys.path:
        sys.path.insert(0, path)


def _update_templates(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    renderers.load_templates()


def _update_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not MkAPIPlugin.nav:
        _create_nav(config, plugin)
        _update_nav(config, plugin)
        MkAPIPlugin.nav = config.nav
    else:
        config.nav = MkAPIPlugin.nav


def _update_extensions(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    for name in [
        "admonition",
        "attr_list",
        "def_list",
        "md_in_html",
        "pymdownx.superfences",
    ]:
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

    page = _get_function("page_title", plugin)
    section = _get_function("section_title", plugin)

    def _create_page(name: str, path: str, filters: list[str], depth: int) -> str:
        MkAPIPlugin.api_uris.append(path)
        abs_path = Path(config.docs_dir) / path
        _check_path(abs_path)
        create_object_page(f"{name}.**", abs_path, [*filters, "sourcelink"])

        path = plugin.config.src_dir + "/" + name.replace(".", "/") + ".md"
        MkAPIPlugin.api_srcs.append(path)
        abs_path = Path(config.docs_dir) / path
        _check_path(abs_path)
        create_source_page(f"{name}.**", abs_path, filters)

        return page(name, depth) if page else name

    def predicate(name: str) -> bool:
        return any(ex not in name for ex in plugin.config.exclude)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with Halo(text="Updating nav...", spinner="dots"):
            mkapi.nav.update(config.nav, _create_page, section, predicate)


# def _on_config_plugin(config: MkDocsConfig, plugin: MkAPIPlugin) -> MkDocsConfig:
#     if func := _get_function("on_config", plugin):
#         msg = f"Calling {plugin.config.on_config!r}"
#         logger.info(msg)
#         config_ = func(config, plugin)
#         if isinstance(config_, MkDocsConfig):
#             return config_
#     return config


def _collect_theme_files(config: MkDocsConfig, plugin: MkAPIPlugin) -> list[File]:
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


def _replace_toc(toc: TableOfContents | list[AnchorLink]) -> None:
    for link in toc:
        link.id = link.id.replace("\0295\03", "_")
        link.title = re.sub(r"\s+\[.+?\]", "", link.title)  # Remove source link.
        link.title = link.title.split(".")[-1]  # Remove prefix.
        _replace_toc(link.children)
