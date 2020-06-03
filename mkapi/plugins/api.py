import atexit
import importlib
import inspect
import logging
import os
import shutil
import sys
from typing import Iterator, List

from mkapi.core.node import get_node
from mkapi.core.renderer import renderer

logger = logging.getLogger("mkdocs")


def create_nav(config):
    nav = config["nav"]
    docs_dir = config["docs_dir"]
    config_dir = os.path.dirname(config["config_file_path"])
    for page in nav:
        if isinstance(page, dict):
            for key, value in page.items():
                if isinstance(value, str) and value.startswith("mkapi/"):
                    page[key] = walk(value, docs_dir, config_dir)
    return config


def _walk(top: str) -> Iterator[List[str]]:
    for root, dirs, files in os.walk(top):
        paths = [root]
        for x in dirs:
            if x.startswith("__"):
                dirs.remove(x)
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                paths.append(file[:-3])
        yield paths


def walk(value: str, docs_dir: str, config_dir) -> list:
    _, api_path, *tops = value.split("/")
    abs_api_path = os.path.join(docs_dir, api_path)
    if os.path.exists(abs_api_path):
        logger.error(f'[MkApi] {abs_api_path} exists: Delete manually for safety.')
        sys.exit(1)
    os.mkdir(abs_api_path)
    atexit.register(lambda path=abs_api_path: rmtree(path))

    top = os.path.join(config_dir, *tops)
    root = os.path.dirname(top)

    if root not in sys.path:
        sys.path.insert(0, root)
    nav = []
    for paths in _walk(top):
        package = os.path.relpath(paths[0], root)
        package = package.replace("/", ".").replace("\\", ".")
        pages = []
        package_obj = importlib.import_module(package)
        if inspect.getdoc(package_obj):
            paths[0] = ""
        else:
            paths = paths[1:]

        for path in paths:
            if path:
                module = ".".join([package, path])
            else:
                module = package
            abs_path = "/".join([abs_api_path, module]) + ".md"
            create_page(abs_path, module)
            page = os.path.relpath(abs_path, docs_dir).replace("\\", "/")
            pages.append(page)
        nav.append({package: pages})

    return nav


def rmtree(path):
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except PermissionError:
        logger.warning(f"[MkApi] Couldn't delete directory: {path}")


def create_page(abs_path, module: str):
    with open(abs_path, "w") as f:
        f.write(create_markdown(module))


def create_markdown(module: str) -> str:
    node = get_node(module, max_depth=1)
    members = [member.id for member in node.members]
    markdown = renderer.render_page(node, module, members)
    return markdown
