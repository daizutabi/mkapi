"""MkAPI Plugin class.

MkAPI Plugin is a MkDocs plugin that creates Python API documentation
from Docstring.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import Files, get_files

import mkapi
from mkapi import renderers
from mkapi.nav import update_nav
from mkapi.pages import Page as MkAPIPage
from mkapi.pages import collect_objects
from mkapi.utils import is_package

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.structure.pages import Page as MkDocsPage
    # from mkdocs.structure.toc import AnchorLink, TableOfContents
    # from mkdocs.utils.templates import TemplateContext
    # from mkdocs.structure.nav import Navigation

logger = get_plugin_logger("MkAPI")


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

    nav: list | None = None

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


def _get_function(name: str, plugin: MkAPIPlugin) -> Callable | None:
    if fullname := plugin.config.get(name, None):
        module_name, func_name = fullname.rsplit(".", maxsplit=1)
        module = importlib.import_module(module_name)
        return getattr(module, func_name)
    return None


def _insert_sys_path(config: MkAPIConfig) -> None:
    config_dir = Path(config.config_file_path).parent
    for src_dir in config.src_dirs:
        path = os.path.normpath(config_dir / src_dir)
        if path not in sys.path:
            sys.path.insert(0, path)


def _update_templates(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    renderers.load_templates()


def _update_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    if not MkAPIPlugin.nav:
        _update_nav(config, plugin)
        MkAPIPlugin.nav = config.nav
    else:
        config.nav = MkAPIPlugin.nav


def _update_nav(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    page = _get_function("page_title", plugin)
    section = _get_function("section_title", plugin)

    def create_page(name: str, depth: int, path: str, filters: list[str]) -> str:
        abs_path = Path(config.docs_dir) / path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        collect_objects(name, abs_path)
        with abs_path.open("w") as file:
            file.write(renderers.render_module(name, filters))
        return page(name, depth, is_package(name)) if page else name

    def predicate(name: str) -> bool:
        return any(ex not in name for ex in plugin.config.exclude)

    if config.nav:
        config.nav = update_nav(config.nav, create_page, section, predicate)


def _on_config_plugin(config: MkDocsConfig, plugin: MkAPIPlugin) -> MkDocsConfig:
    if func := _get_function("on_config", plugin):
        msg = f"Calling user 'on_config': {plugin.config.on_config}"
        logger.info(msg)
        config_ = func(config, plugin)
        if isinstance(config_, MkDocsConfig):
            return config_
    return config


# def _clear_prefix(
#     toc: TableOfContents | list[AnchorLink],
#     name: str,
#     level: int,
# ) -> None:
#     """Clear prefix."""
#     for toc_item in toc:
#         if toc_item.level >= level and (not name or toc_item.title == name):
#             toc_item.title = toc_item.title.split(".")[-1]
#         _clear_prefix(toc_item.children, "", level)


# def _clean_page_title(page: MkDocsPage) -> None:
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

# def create_source_page(path: Path, module: Module, filters: list[str]) -> None:
#     """Create a page for source."""
#     filters_str = "|".join(filters)
#     with path.open("w") as f:
#         f.write(f"# ![mkapi]({module.object.id}|code|{filters_str})")
