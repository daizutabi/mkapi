"""MkAPI Plugin class.

MkAPI Plugin is a MkDocs plugin that creates Python API documentation
from Docstring.
"""
import atexit
import inspect
import logging
import os
import re
import shutil
import sys
from pathlib import Path

import yaml
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files

import mkapi
from mkapi.core.filter import split_filters, update_filters
from mkapi.core.module import Module, get_module
from mkapi.core.object import get_object
from mkapi.core.page import Page

logger = logging.getLogger("mkdocs")
global_config = {}


class MkapiConfig(Config):
    """Specify the config schema."""

    src_dirs = config_options.Type(list[str], default=[])
    on_config = config_options.Type(str, default="")
    filters = config_options.Type(list[str], default=[])
    callback = config_options.Type(str, default="")


class MkapiPlugin(BasePlugin[MkapiConfig]):
    """MkapiPlugin class for API generation."""

    server = None

    def on_config(self, config: MkapiConfig, **kwargs) -> MkapiConfig:
        """Insert `src_dirs` to `sys.path`."""
        config_dir = Path(config.config_file_path).parent
        for src_dir in self.config.src_dirs:
            if (path := os.path.normpath(config_dir / src_dir)) not in sys.path:
                sys.path.insert(0, path)
        if not self.config.src_dirs and (path := Path.cwd()) not in sys.path:
            sys.path.insert(0, str(path))
        self.pages, self.abs_api_paths = {}, []
        if not self.server:
            config, self.abs_api_paths = create_nav(config, self.config.filters)
            global_config["config"] = config
            global_config["abs_api_paths"] = self.abs_api_paths
        else:
            config = global_config["config"]
            self.abs_api_paths = global_config["abs_api_paths"]

        if self.config.on_config:
            on_config = get_object(self.config.on_config)
            kwargs = {}
            params = inspect.signature(on_config).parameters
            if "config" in params:
                kwargs["config"] = config
            if "mkapi" in params:
                kwargs["mkapi"] = self
            msg = f"[MkAPI] Calling user 'on_config' with {list(kwargs)}"
            logger.info(msg)
            config_ = on_config(**kwargs)
            if config_ is not None:
                config = config_

        if "admonition" not in config["markdown_extensions"]:
            config["markdown_extensions"].append("admonition")

        return config

    def on_files(self, files, config: MkapiConfig, **kwargs):
        """Collect plugin CSS/JavaScript and appends them to `files`."""
        root = Path(mkapi.__file__).parent / "theme"
        docs_dir = config["docs_dir"]
        config["docs_dir"] = root
        files_ = get_files(config)
        config["docs_dir"] = docs_dir
        theme_name = config["theme"].name

        css = []
        js = []
        for file in files_:
            path = file.src_path.replace("\\", "/")
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
        css = [x for x in css if x not in config["extra_css"]]
        js = [x for x in js if x not in config["extra_javascript"]]
        config["extra_css"] = css + config["extra_css"]
        config["extra_javascript"] = js + config["extra_javascript"]

        return files

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        """Convert Markdown source to intermidiate version."""
        abs_src_path = page.file.abs_src_path
        clean_page_title(page)
        page = Page(
            markdown,
            abs_src_path,
            self.abs_api_paths,
            filters=self.config["filters"],
        )
        self.pages[abs_src_path] = page
        return page.markdown

    def on_page_content(self, html, page, config, files, **kwargs):
        """Merge HTML and MkAPI's node structure."""
        if page.title:
            page.title = re.sub(r"<.*?>", "", page.title)
        abs_src_path = page.file.abs_src_path
        page = self.pages[abs_src_path]
        return page.content(html)

    def on_page_context(self, context, page, config, nav, **kwargs):
        abs_src_path = page.file.abs_src_path
        if abs_src_path in self.abs_api_paths:
            clear_prefix(page.toc, 2)
        else:
            for level, id_ in self.pages[abs_src_path].headings:
                clear_prefix(page.toc, level, id_)
        return context

    def on_serve(self, server, config, builder, **kwargs):
        for path in ["theme", "templates"]:
            server.watch(Path(mkapi.__file__) / path, builder)
        self.__class__.server = server
        return server


def create_nav(
    config: MkapiConfig,
    filters: list[str],
) -> tuple[MkapiConfig, list[str]]:
    """Create nav."""
    nav = config["nav"]
    docs_dir = config["docs_dir"]
    config_dir = Path(config.config_file_path).parent
    abs_api_paths: list[str] = []
    for page in nav:
        if isinstance(page, dict):
            for key, value in page.items():
                if isinstance(value, str) and value.startswith("mkapi/"):
                    _ = collect(value, docs_dir, config_dir, filters)
                    page[key], abs_api_paths_ = _
                    abs_api_paths.extend(abs_api_paths_)
    return config, abs_api_paths


def collect(
    path: str,
    docs_dir: str,
    config_dir: Path,
    global_filters: list[str],
) -> tuple[list, list]:
    """Collect pages."""
    _, api_path, *paths, package_path = path.split("/")
    abs_api_path = Path(docs_dir) / api_path
    if abs_api_path.exists():
        msg = f"[MkAPI] {abs_api_path} exists: Delete manually for safety."
        logger.error(msg)
        sys.exit(1)
    Path.mkdir(abs_api_path / "source", parents=True)
    atexit.register(lambda path=abs_api_path: rmtree(path))

    if (root := config_dir.joinpath(*paths)) not in sys.path:
        sys.path.insert(0, str(root))

    package_path, filters = split_filters(package_path)
    filters = update_filters(global_filters, filters)

    nav = []
    abs_api_paths: list[Path] = []
    modules: dict[str, str] = {}
    package = None

    def add_page(module: Module, package: str | None) -> None:
        page_file = module.object.id + ".md"
        abs_path = abs_api_path / page_file
        abs_api_paths.append(abs_path)
        create_page(abs_path, module, filters)
        page_name = module.object.id
        if package and "short_nav" in filters and page_name != package:
            page_name = page_name[len(package) + 1 :]
        modules[page_name] = str(Path(api_path) / page_file)
        abs_path = abs_api_path / "source" / page_file
        create_source_page(abs_path, module, filters)

    module = get_module(package_path)
    for m in module:
        if m.object.kind == "package":
            if package and modules:
                nav.append({package: modules})
            package = m.object.id
            modules.clear()
            if m.docstring or any(s.docstring for s in m.members):
                add_page(m, package)
        else:
            add_page(m, package)
    if package and modules:
        nav.append({package: modules})

    return nav, abs_api_paths


def create_page(path: Path, module: Module, filters: list[str]) -> None:
    """Create a page."""
    with path.open("w") as f:
        f.write(module.get_markdown(filters))


def create_source_page(path: Path, module: Module, filters: list[str]) -> None:
    """Create a page for source."""
    filters_str = "|".join(filters)
    with path.open("w") as f:
        f.write(f"# ![mkapi]({module.object.id}|code|{filters_str})")


def clear_prefix(toc, level: int, id_: str = "") -> None:
    """Clear prefix."""
    for toc_item in toc:
        if toc_item.level >= level and (not id_ or toc_item.title == id_):
            toc_item.title = toc_item.title.split(".")[-1]
        clear_prefix(toc_item.children, level)


def clean_page_title(page) -> None:
    """Clean page title."""
    title = page.title
    if title.startswith("![mkapi]("):
        page.title = title[9:-1].split("|")[0]


def rmtree(path: Path) -> None:
    """Delete directory created by MkAPI."""
    if not path.exists():
        return
    try:
        shutil.rmtree(path)
    except PermissionError:
        msg = f"[MkAPI] Couldn't delete directory: {path}"
        logger.warning(msg)
