"""Configuration for MkAPI."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from astdoc.utils import cache
from mkdocs.config import Config as BaseConfig
from mkdocs.config import config_options

if TYPE_CHECKING:
    from collections.abc import Callable


class Config(BaseConfig):
    """Configuration for MkAPI."""

    config = config_options.Type(str, default="")
    exclude = config_options.Type(list, default=[])
    debug = config_options.Type(bool, default=False)
    search_exclude = config_options.Type(bool, default=False)
    source_search_exclude = config_options.Type(bool, default=True)
    save = config_options.Type(bool, default=False)


_config: Config = Config()  # type: ignore


def set_config(config: Config) -> None:
    """Set the config object."""
    global _config  # noqa: PLW0603
    _config = config


def get_config() -> Config:
    """Get the config object."""
    return _config


@cache
def get_function(name: str) -> Callable | None:
    """Get a function by name from the config file."""
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
