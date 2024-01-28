"""Markdown utility."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from mkapi.utils import join_without_first_indent

if TYPE_CHECKING:
    from collections.abc import Iterator


# TODO: use `doctest` library.
def _splitter(text: str) -> Iterator[str]:
    start = 0
    in_code = False
    lines = text.split("\n")
    for stop, line in enumerate(lines, 1):
        if ">>>" in line and not in_code:
            if start < stop - 1:
                yield "\n".join(lines[start : stop - 1])
            start = stop - 1
            in_code = True
        elif not line.strip() and in_code:
            yield join_without_first_indent(lines, start, stop)
            start = stop
            in_code = False
    if start < len(lines):
        yield join_without_first_indent(lines, start, len(lines))


def add_fence(text: str) -> str:
    """Add fence in `>>>` statements."""
    blocks = []
    for block in _splitter(text):
        _ = f"~~~python\n{block}\n~~~\n" if block.startswith(">>>") else block
        blocks.append(_)
    return "\n".join(blocks).strip()
