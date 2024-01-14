"""Utility code."""
from __future__ import annotations

import re
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator


def get_module_path(name: str) -> Path | None:
    """Return the source path of the module name."""
    try:
        spec = find_spec(name)
    except ModuleNotFoundError:
        return None
    if not spec or not hasattr(spec, "origin") or not spec.origin:
        return None
    path = Path(spec.origin)
    if not path.exists():  # for builtin, frozen
        return None
    return path


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


def is_package(name: str) -> bool:
    """Return True if the name is a package."""
    if (spec := find_spec(name)) and spec.origin:
        return Path(spec.origin).stem == "__init__"
    return False


def iter_submodulenames(name: str) -> Iterator[str]:
    """Yield submodule names."""
    spec = find_spec(name)
    if not spec or not spec.submodule_search_locations:
        return
    for location in spec.submodule_search_locations:
        for path in Path(location).iterdir():
            if _is_module(path):
                yield f"{name}.{path.stem}"


def find_submodulenames(
    name: str,
    predicate: Callable[[str], bool] | None = None,
) -> list[str]:
    """Return a list of submodule names.

    Optionally, only return submodules that satisfy a given predicate.
    """
    predicate = predicate or (lambda _: True)
    names = [name for name in iter_submodulenames(name) if predicate(name)]
    names.sort(key=lambda x: not is_package(x))
    return names


def iter_parent_modulenames(fullname: str, *, reverse: bool = False) -> Iterator[str]:
    """Yield parent module names.

    Examples:
        >>> list(iter_parent_modulenames("a.b.c.d"))
        ['a', 'a.b', 'a.b.c', 'a.b.c.d']
        >>> list(iter_parent_modulenames("a.b.c.d", reverse=True))
        ['a.b.c.d', 'a.b.c', 'a.b', 'a']
    """
    names = fullname.split(".")
    it = range(len(names), 0, -1) if reverse else range(1, len(names) + 1)
    for k in it:
        yield ".".join(names[:k])


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


def join_without_first_indent(
    lines: list[str] | str,
    start: int = 0,
    stop: int | None = None,
) -> str:
    r"""Return a joint string without first indent.

    Examples:
        >>> join_without_first_indent(["abc", "def"])
        'abc\ndef'
        >>> join_without_first_indent(["  abc", "  def"])
        'abc\ndef'
        >>> join_without_first_indent(["  abc", "    def  ", ""])
        'abc\n  def'
        >>> join_without_first_indent(["  abc", "    def", "    ghi"])
        'abc\n  def\n  ghi'
        >>> join_without_first_indent(["  abc", "    def", "    ghi"], stop=2)
        'abc\n  def'
        >>> join_without_first_indent([])
        ''
    """
    if not lines:
        return ""
    if isinstance(lines, str):
        return join_without_first_indent(lines.split("\n"))
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
            yield join_without_first_indent(lines, start, stop)
            start = stop
            in_code = False
    if start < len(lines):
        yield join_without_first_indent(lines, start, len(lines))


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


def get_by_name[T](items: Iterable[T], name: str, attr: str = "name") -> T | None:  # noqa: D103
    for item in items:
        if getattr(item, attr, None) == name:
            return item
    return None


def get_by_kind[T](items: Iterable[T], kind: str) -> T | None:  # noqa: D103
    return get_by_name(items, kind, attr="kind")


def get_by_type[T](items: Iterable, type_: type[T]) -> T | None:  # noqa: D103
    for item in items:
        if isinstance(item, type_):
            return item
    return None


def del_by_name[T](items: list[T], name: str, attr: str = "name") -> None:  # noqa: D103
    for k, item in enumerate(items):
        if getattr(item, attr, None) == name:
            del items[k]
            return


def unique_names(a: Iterable, b: Iterable, attr: str = "name") -> list[str]:  # noqa: D103
    names = [getattr(x, attr) for x in a]
    for x in b:
        if (name := getattr(x, attr)) not in names:
            names.append(name)
    return names


def split_filters(name: str) -> tuple[str, list[str]]:
    """Split filters written after `|`s.

    Examples:
        >>> split_filters("a.b.c")
        ('a.b.c', [])
        >>> split_filters("a.b.c|upper|strict")
        ('a.b.c', ['upper', 'strict'])
        >>> split_filters("|upper|strict")
        ('', ['upper', 'strict'])
        >>> split_filters("")
        ('', [])
    """
    index = name.find("|")
    if index == -1:
        return name, []
    name, filters = name[:index], name[index + 1 :]
    return name, filters.split("|")


def update_filters(org: list[str], update: list[str]) -> list[str]:
    """Update filters.

    Examples:
        >>> update_filters(['upper'], ['lower'])
        ['lower']
        >>> update_filters(['lower'], ['upper'])
        ['upper']
        >>> update_filters(['long'], ['short'])
        ['short']
        >>> update_filters(['short'], ['long'])
        ['long']
    """
    filters = org + update
    for x, y in [["lower", "upper"], ["long", "short"]]:
        if x in org and y in update:
            del filters[filters.index(x)]
        if y in org and x in update:
            del filters[filters.index(y)]
    return filters
