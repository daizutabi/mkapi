"""Utility code."""
from __future__ import annotations

import re
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def _is_module(path: Path, exclude_patterns: Iterable[str] = ()) -> bool:
    path_str = path.as_posix()
    for pattern in exclude_patterns:
        if re.search(pattern, path_str):
            return False
    it = (p.name for p in path.iterdir())
    if path.is_dir() and "__init__.py" in it:
        return True
    if path.is_file() and not path.stem.startswith("__") and path.suffix == ".py":
        return True
    return False


def _is_package(name: str) -> bool:
    if (spec := find_spec(name)) and spec.origin:
        return Path(spec.origin).stem == "__init__"
    return False


def iter_submodule_names(name: str) -> Iterator[str]:
    """Yield submodule names."""
    spec = find_spec(name)
    if not spec or not spec.submodule_search_locations:
        return
    for location in spec.submodule_search_locations:
        for path in Path(location).iterdir():
            if _is_module(path):
                yield f"{name}.{path.stem}"


def find_submodule_names(name: str) -> list[str]:
    """Return a list of submodules."""
    names = iter_submodule_names(name)
    return sorted(names, key=lambda name: not _is_package(name))


def split_type(markdown: str) -> tuple[str, str]:
    """Return a tuple of (type, markdown) splitted by a colon.

    Examples:
        >>> split_type("int : Integer value.")
        ('int', 'Integer value.')
        >>> split_type("abc")
        ('', 'abc')
        >>> split_type("")
        ('', '')
    """
    line = markdown.split("\n", maxsplit=1)[0]
    if (index := line.find(":")) != -1:
        type_ = line[:index].strip()
        markdown = markdown[index + 1 :].strip()
        return type_, markdown
    return "", markdown


def delete_ptags(html: str) -> str:
    """Return HTML without <p> tag.

    Examples:
        >>> delete_ptags("<p>para1</p><p>para2</p>")
        'para1<br>para2'
    """
    html = html.replace("<p>", "").replace("</p>", "<br>")
    if html.endswith("<br>"):
        html = html[:-4]
    return html


def get_indent(line: str) -> int:
    """Return the number of indent of a line.

    Examples:
        >>> get_indent("abc")
        0
        >>> get_indent("  abc")
        2
        >>> get_indent("")
        -1
    """
    for k, x in enumerate(line):
        if x != " ":
            return k
    return -1


def join_without_indent(
    lines: list[str] | str,
    start: int = 0,
    stop: int | None = None,
) -> str:
    r"""Return a joint string without indent.

    Examples:
        >>> join_without_indent(["abc", "def"])
        'abc\ndef'
        >>> join_without_indent(["  abc", "  def"])
        'abc\ndef'
        >>> join_without_indent(["  abc", "    def  ", ""])
        'abc\n  def'
        >>> join_without_indent(["  abc", "    def", "    ghi"])
        'abc\n  def\n  ghi'
        >>> join_without_indent(["  abc", "    def", "    ghi"], stop=2)
        'abc\n  def'
        >>> join_without_indent([])
        ''
    """
    if not lines:
        return ""
    if isinstance(lines, str):
        return join_without_indent(lines.split("\n"))
    indent = get_indent(lines[start])
    return "\n".join(line[indent:] for line in lines[start:stop]).strip()


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
            yield join_without_indent(lines, start, stop)
            start = stop
            in_code = False
    if start < len(lines):
        yield join_without_indent(lines, start, len(lines))


def add_fence(text: str) -> str:
    """Add fence in `>>>` statements."""
    blocks = []
    for block in _splitter(text):
        if block.startswith(">>>"):
            block = f"~~~python\n{block}\n~~~\n"  # noqa: PLW2901
        blocks.append(block)
    return "\n".join(blocks).strip()


def add_admonition(name: str, markdown: str) -> str:
    """Add admonition in note and/or warning sections."""
    if name.startswith("Note"):
        kind = "note"
    elif name.startswith("Warning"):
        kind = "warning"
    else:
        kind = name.lower()
    lines = ["    " + line if line else "" for line in markdown.split("\n")]
    lines.insert(0, f'!!! {kind} "{name}"')
    return "\n".join(lines)
