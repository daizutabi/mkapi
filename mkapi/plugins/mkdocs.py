"""This module provides the MkapiPlugin class.

MkapiPlugin is a MkDocs plugin that creates Python API documentation from Docstring.
"""
import inspect
import logging
import os
import re
import sys

import yaml
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files

import mkapi
import mkapi.plugins.api
from mkapi.core.object import get_object
from mkapi.core.page import Page

logger = logging.getLogger("mkdocs")
global_config = {}


class MkapiPlugin(BasePlugin):
    """MkapiPlugin class for API generation."""

    config_scheme = (
        ("src_dirs", config_options.Type(list, default=[])),
        ("on_config", config_options.Type(str, default="")),
        ("callback", config_options.Type(str, default="")),
    )
    server = None

    def on_config(self, config):
        """Inserts `src_dirs` to `sys.path`."""
        config_dir = os.path.dirname(config["config_file_path"])
        for src_dir in self.config["src_dirs"]:
            path = os.path.normpath(os.path.join(config_dir, src_dir))
            if path not in sys.path:
                sys.path.insert(0, path)
        if not self.config["src_dirs"]:
            path = os.getcwd()
            if path not in sys.path:
                sys.path.insert(0, path)
        self.pages = {}
        self.abs_api_paths = []
        if not self.server:
            config, self.abs_api_paths = mkapi.plugins.api.create_nav(config)
            global_config["config"] = config
            global_config["abs_api_paths"] = self.abs_api_paths
        else:
            config = global_config["config"]
            self.abs_api_paths = global_config["abs_api_paths"]

        if self.config["on_config"]:
            on_config = get_object(self.config["on_config"])
            kwargs = {}
            params = inspect.signature(on_config).parameters
            if "config" in params:
                kwargs["config"] = config
            if "mkapi" in params:
                kwargs["mkapi"] = self
            logger.info(f"[MkApi] Calling user 'on_config' with {list(kwargs)}")
            config_ = on_config(**kwargs)
            if config_ is not None:
                config = config_

        ext = config["markdown_extensions"]
        if "admonition" not in ext:
            config["markdown_extensions"].append("admonition")

        return config

    def on_files(self, files, config):
        """Collects plugin CSS ans JavaScript and appends them to `files`."""
        root = os.path.join(os.path.dirname(mkapi.__file__), "theme")
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
                path = os.path.normpath(os.path.join(root, path))
                with open(path) as f:
                    data = yaml.safe_load(f)
                css = data.get("extra_css", []) + css
                js = data.get("extra_javascript", []) + js
        css = [x for x in css if x not in config["extra_css"]]
        js = [x for x in js if x not in config["extra_javascript"]]
        config["extra_css"] = css + config["extra_css"]
        config["extra_javascript"] = js + config["extra_javascript"]

        return files

    def on_page_markdown(self, markdown, page, config, files):
        """Converts Markdown source to intermidiate version."""
        abs_src_path = page.file.abs_src_path
        clean_page_title(page)
        page = Page(markdown, abs_src_path, self.abs_api_paths)
        self.pages[abs_src_path] = page
        return page.markdown

    def on_page_content(self, html, page, config, files):
        """Merges html and MkApi's node structure."""
        if page.title:
            page.title = re.sub(r"<.*?>", "", page.title)
        abs_src_path = page.file.abs_src_path
        page = self.pages[abs_src_path]
        return page.content(html)

    def on_page_context(self, context, page, config, nav):
        abs_src_path = page.file.abs_src_path
        if abs_src_path in self.abs_api_paths:
            clear_prefix(page.toc, 2)
        return context

    def on_serve(self, server, config, builder):
        for path in ["theme", "templates"]:
            root = os.path.join(os.path.dirname(mkapi.__file__), path)
            server.watch(root, builder)
        self.__class__.server = server
        return server


def clear_prefix(toc, level: int):
    for toc_item in toc:
        if toc_item.level >= level:
            toc_item.title = toc_item.title.split(".")[-1]
        clear_prefix(toc_item.children, level)
    return


def clean_page_title(page):
    title = page.title
    if title.startswith("![mkapi]("):
        page.title = title[9:-1].split("|")[0]
