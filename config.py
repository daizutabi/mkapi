"""Config functions."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from mkapi.plugin import Plugin


def before_on_config(config: MkDocsConfig, plugin: Plugin) -> None:
    """Called before `on_config` event of MkAPI plugin."""
    if "." not in sys.path:
        sys.path.insert(0, ".")


def after_on_config(config: MkDocsConfig, plugin: Plugin) -> None:
    """Called after `on_config` event of MkAPI plugin."""


def page_title(name: str, depth: int) -> str:
    """Return a page title."""
    return name
    # return ".".join(name.split(".")[depth:])  # noqa: ERA001


def section_title(name: str, depth: int) -> str:
    """Return a section title."""
    return name
    # return ".".join(name.split(".")[depth:])  # noqa: ERA001


def toc_title(name: str, depth: int) -> str:
    """Return a toc title."""
    return name.split(".")[-1]  # Remove prefix.
