"""Config functions."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from mkapi.plugin import MkAPIPlugin


def before_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:  # noqa: ARG001
    """Called before `on_config` event of MkAPI plugin."""
    if "." not in sys.path:
        sys.path.insert(0, "tests")


def after_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:  # noqa: ARG001
    """Called after `on_config` event of MkAPI plugin."""


def page_title(name: str, depth: int) -> str:  # noqa: ARG001
    """Return a page title."""
    return name
    # return ".".join(name.split(".")[depth:])


def section_title(name: str, depth: int) -> str:  # noqa: ARG001
    """Return a section title."""
    return name
    # return ".".join(name.split(".")[depth:])


def toc_title(name: str, depth: int) -> str:  # noqa: ARG001
    """Return a toc title."""
    return name.split(".")[-1]  # Remove prefix.
