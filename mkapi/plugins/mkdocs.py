import logging
import os
import re
import sys

import yaml
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import get_files

import mkapi
import mkapi.core.converter

logger = logging.getLogger("mkdocs")


class MkapiPlugin(BasePlugin):
    config_scheme = (
        ("autoapi_dirs", config_options.Type(list, default=["."])),
        ("dirty", config_options.Type(bool, default=False)),
    )
    converter = mkapi.core.converter.Converter()

    def on_config(self, config):
        logger.info(f"[MkAPI] Current directory: {os.getcwd()}")
        logger.info(f"[MkAPI] Watching directories: {self.config['autoapi_dirs']}")
        paths = []
        for path in self.config["autoapi_dirs"]:
            path = os.path.join(os.getcwd(), path)
            path = os.path.normpath(path)
            paths.append(path)
            sys.path.insert(0, path)
        self.config["paths"] = paths
        self.converter.dirty = self.config["dirty"]
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

    def on_nav(self, nav, config, files):
        paths = [page.file.abs_src_path for page in nav.pages]
        logger.info(f"[MkAPI] Converting {len(paths)} pages.")
        self.converter.convert_from_files(paths)
        logger.info("[MkAPI] Conversion finished.")
        return nav

    def on_page_read_source(self, page, config):
        try:
            return self.converter.pages[page.file.abs_src_path].source
        except KeyError:
            return

    def on_page_content(self, html, page, config, files):
        return html

    def on_serve(self, server, config, builder):
        watcher = server.watcher
        for root in self.config["paths"]:
            server.watch(root, builder)
        root = os.path.join(os.path.dirname(mkapi.__file__), "theme")
        server.watch(root, builder)
        watcher.ignore_dirs("__pycache__")
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
