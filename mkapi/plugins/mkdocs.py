import logging
import os
import re
import sys

import yaml
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files

import mkapi
import mkapi.plugins.preprocess
from mkapi.core.page import Page

logger = logging.getLogger("mkdocs")


class MkapiPlugin(BasePlugin):
    config_scheme = (
        ("api_dir", config_options.Type(str, default="api")),
        ("src_dir", config_options.Type(str, default="")),
    )

    def on_config(self, config):
        self.pages = {}
        api_dir = os.path.join(config["docs_dir"], self.config["api_dir"])
        dirname = os.path.dirname(config["config_file_path"])
        nav = config["nav"]
        for page in nav:
            for key, value in page.items():
                if isinstance(value, str) and value.startswith("mkapi:"):
                    root = value.split(":")[1]
                    root = os.path.join(dirname, root)
                    contents = mkapi.plugins.preprocess.make_pages(root, api_dir)
                    page[key] = contents
        src_dir = self.config["src_dir"]
        if src_dir and src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        return config

    def on_files(self, files, config):
        root = os.path.join(os.path.dirname(mkapi.__file__), "theme")
        docs_dir = config["docs_dir"]
        config["docs_dir"] = root
        files_ = get_files(config)
        config["docs_dir"] = docs_dir

        css = []
        js = []
        for file in files_:
            path = file.src_path.replace("\\", "/")
            if path.endswith(".css"):
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

        for file in files:
            normalize_file(file, config)

        return files

    def on_page_markdown(self, markdown, page, config, files):
        path = page.file.abs_src_path
        page = Page(markdown)
        self.pages[path] = page
        return page.markdown

    def on_page_content(self, html, page, config, files):
        path = page.file.abs_src_path
        page = self.pages[path]
        return page.content(html)

    def on_serve(self, server, config, builder):
        for path in ["theme", "templates"]:
            root = os.path.join(os.path.dirname(mkapi.__file__), path)
            server.watch(root, builder)
        return server


NORMALIZE_PATTERN = re.compile(r"(^|[\\/])\w*[0-9]+[._ ](.*?)")


def normalize_file(file, config):
    if file.dest_path.endswith(".html"):
        file.dest_path = NORMALIZE_PATTERN.sub(r"\1\2", file.dest_path)
        file.dest_path = file.dest_path.replace(" ", "_")
        file.abs_dest_path = os.path.normpath(
            os.path.join(config["site_dir"], file.dest_path)
        )
        file.url = NORMALIZE_PATTERN.sub(r"\1\2", file.url)
        file.url = file.url.replace(" ", "_")
