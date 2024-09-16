from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.config import Config, config_options

from mkapi.utils import cache

if TYPE_CHECKING:
    from collections.abc import Callable


class MkApiConfig(Config):
    config = config_options.Type(str, default="")
    exclude = config_options.Type(list, default=[])
    src_dir = config_options.Type(str, default="src")
    docs_anchor = config_options.Type(str, default="docs")
    src_anchor = config_options.Type(str, default="source")
    debug = config_options.Type(bool, default=False)


_config: MkApiConfig = MkApiConfig()  # type: ignore


def set_config(config: MkApiConfig):
    global _config
    _config = config


def get_config() -> MkApiConfig:
    return _config


@cache
def get_function(name: str) -> Callable | None:
    config = get_config()
    if not (path_str := config.config):
        return None

    if not path_str.endswith(".py"):
        module = importlib.import_module(path_str)
    else:
        path = Path(path_str)
        if not path.is_absolute():
            path = Path(config.config_file_path).parent / path

        directory = path.parent.as_posix()
        sys.path.insert(0, directory)
        module = importlib.import_module(path.stem)
        del sys.path[0]

    return getattr(module, name, None)
