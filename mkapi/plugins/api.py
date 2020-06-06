import atexit
import importlib
import inspect
import logging
import os
import shutil
import sys
from typing import Iterator, List, Tuple

from mkapi.core.module import get_module
from mkapi.core.node import get_node
from mkapi.core.renderer import renderer

logger = logging.getLogger("mkdocs")


def create_nav(config):
    nav = config["nav"]
    docs_dir = config["docs_dir"]
    config_dir = os.path.dirname(config["config_file_path"])
    api_roots = []
    for page in nav:
        if isinstance(page, dict):
            for key, value in page.items():
                if isinstance(value, str) and value.startswith("mkapi/"):
                    page[key], pages = collect(value, docs_dir, config_dir)
                    api_roots.extend(pages)
    return config, api_roots


def collect(path: str, docs_dir: str, config_dir) -> Tuple[list, list]:
    _, api_path, *paths, package = path.split("/")
    abs_api_path = os.path.join(docs_dir, api_path)
    if os.path.exists(abs_api_path):
        logger.error(f"[MkApi] {abs_api_path} exists: Delete manually for safety.")
        sys.exit(1)
    os.mkdir(abs_api_path)
    atexit.register(lambda path=abs_api_path: rmtree(path))

    root = os.path.join(config_dir, *paths)
    if root not in sys.path:
        sys.path.insert(0, root)

    nav = []
    pages_all = []
    for paths in walk(top):
        package = os.path.relpath(paths[0], root)
        package = package.replace("/", ".").replace("\\", ".")
        package_obj = importlib.import_module(package)
        if inspect.getdoc(package_obj):
            paths[0] = ""
        else:
            paths = paths[1:]

        pages = []
        for path in paths:
            if path:
                module = ".".join([package, path])
                module_obj = importlib.import_module(module)
                if not inspect.getdoc(module_obj):
                    continue
            else:
                module = package
            abs_path = os.path.normpath("/".join([abs_api_path, module]) + ".md")
            if path == "":
                children = paths[1:]
            else:
                children = []
            create_page(abs_path, module, children)
            page = os.path.relpath(abs_path, docs_dir).replace("\\", "/")
            pages_all.append(abs_path)
            pages.append({page[:-3].split(".")[-1]: page})
        if pages:
            nav.append({package: pages})

    return nav, pages_all


def rmtree(path):
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except PermissionError:
        logger.warning(f"[MkApi] Couldn't delete directory: {path}")


def create_page(abs_path, module: str, children: List[str]):
    with open(abs_path, "w") as f:
        f.write(create_markdown(module, children))


def create_markdown(module: str, children: List[str]) -> str:
    node = get_node(module, max_depth=1)
    members = [member.id for member in node.members]
    markdown = renderer.render_page(node, module, members, children)
    return markdown
