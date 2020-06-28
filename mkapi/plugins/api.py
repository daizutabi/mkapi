import atexit
import logging
import os
import shutil
import sys
from typing import Dict, List, Tuple

from mkapi import utils
from mkapi.core.module import Module, get_module

logger = logging.getLogger("mkdocs")


def create_nav(config, global_filters):
    nav = config["nav"]
    docs_dir = config["docs_dir"]
    config_dir = os.path.dirname(config["config_file_path"])
    abs_api_paths = []
    for page in nav:
        if isinstance(page, dict):
            for key, value in page.items():
                if isinstance(value, str) and value.startswith("mkapi/"):
                    page[key], abs_api_paths_ = collect(
                        value, docs_dir, config_dir, global_filters
                    )
                    abs_api_paths.extend(abs_api_paths_)
    return config, abs_api_paths


def collect(path: str, docs_dir: str, config_dir, global_filters) -> Tuple[list, list]:
    _, api_path, *paths, package_path = path.split("/")
    abs_api_path = os.path.join(docs_dir, api_path)
    if os.path.exists(abs_api_path):
        logger.error(f"[MkApi] {abs_api_path} exists: Delete manually for safety.")
        sys.exit(1)
    os.mkdir(abs_api_path)
    os.mkdir(os.path.join(abs_api_path, "source"))
    atexit.register(lambda path=abs_api_path: rmtree(path))

    root = os.path.join(config_dir, *paths)
    if root not in sys.path:
        sys.path.insert(0, root)

    package_path, filters = utils.split_filters(package_path)
    filters = utils.update_filters(global_filters, filters)

    module = get_module(package_path)
    nav = []
    abs_api_paths = []
    modules: Dict[str, str] = {}
    package = None

    def add_page(module: Module):
        page_file = module.object.id + ".md"
        abs_path = os.path.join(abs_api_path, page_file)
        abs_api_paths.append(abs_path)
        create_page(abs_path, module, filters)
        modules[module.object.id] = os.path.join(api_path, page_file)

        abs_path = os.path.join(abs_api_path, "source", page_file)
        create_source_page(abs_path, module, filters)

    for m in module:
        if m.object.kind == "package":
            if package and modules:
                nav.append({package: modules})
            package = m.object.id
            modules = {}
            if m.docstring or any(s.docstring for s in m.members):
                add_page(m)
        else:
            add_page(m)
    if package and modules:
        nav.append({package: modules})

    return nav, abs_api_paths


def create_page(path: str, module: Module, filters: List[str]):
    with open(path, "w") as f:
        f.write(module.get_markdown(filters))


def create_source_page(path: str, module: Module, filters: List[str]):
    filters_str = "|".join(filters)
    with open(path, "w") as f:
        f.write(f"# ![mkapi]({module.object.id}|code|{filters_str})")


def rmtree(path: str):
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except PermissionError:
        logger.warning(f"[MkApi] Couldn't delete directory: {path}")
