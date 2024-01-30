"""Markdown utility."""
from __future__ import annotations

import doctest
import re
from typing import TYPE_CHECKING

from mkapi.utils import iter_identifiers

if TYPE_CHECKING:
    from collections.abc import Iterator


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


def add_link(text: str) -> str:
    """Add link for a "See Also" section."""
    if ":" in text:
        text = re.sub(r"\n\s+", " ", text)
        text = "\n".join(f"* {line}" for line in text.split("\n"))
    strs = []
    before_colon = True
    for name, isidentifier in iter_identifiers(text):
        if isidentifier and before_colon:
            strs.append(f"[__mkapi__.{name}][]")
        else:
            strs.append(name)
            if ":" in name:
                before_colon = False
            if "\n" in name:
                before_colon = True
    return "".join(strs)


def replace_directives(text: str) -> str:
    """Replace directives."""
    return "\n".join(_split_directives(text))


def _split_directives(text: str) -> Iterator[str]:
    name = ""
    title = ""
    bufs = []
    in_directive = False
    lines = text.split("\n")
    n = len(lines)
    for k, line in enumerate(lines):
        if line.startswith(".. ") and "::" in line:
            name, suffix = (x.strip() for x in line[3:].split("::", maxsplit=1))
            if name == "deprecated" and suffix:
                title = f"Deprecated since version {suffix}"
            else:
                title = ""
            in_directive = True
        elif in_directive:
            if not line or k == n - 1:
                if line:
                    bufs.append(line.strip())
                yield from _get_directive(name, title, "\n".join(bufs))
                in_directive = False
                bufs = []
            else:
                bufs.append(line.strip())
        else:
            yield line


def _get_directive(name: str, title: str, body: str) -> Iterator[str]:
    body = replace_directives(body)
    if name == "code-block":
        yield f"```{{.{title}}}"
        yield from body
        yield "```"
    else:
        yield f'!!! {name} "{title}"' if title else f"!!! {name}"
        for buf in body.split("\n"):
            yield f"    {buf}"


PROMPT_ONLY = re.compile(r"^\>\>\>\s*?$", re.MULTILINE)


def replace_examples(text: str) -> str:
    """Replace examples."""
    if "\n" not in text:
        return text
    text = PROMPT_ONLY.sub(">>> MKAPI_BLANK_LINE", text)
    try:
        examples = doctest.DocTestParser().get_examples(text)
    except ValueError:
        return text
    if not examples:
        return text
    return "\n".join(_split_examples(text, examples))


def _split_examples(text: str, examples: list[doctest.Example]) -> Iterator[str]:
    lines = text.split("\n")
    want = "dummy"
    lineno = 0
    n = len(examples)
    in_example = False
    for k, example in enumerate(examples):
        if example.lineno > lineno:
            if in_example:
                yield "```"
                in_example = False
            yield from lines[lineno : example.lineno]
        if want or not in_example:
            yield "```{.python .mkapi-example-input}"
            in_example = True
        yield example.source[:-1].replace("MKAPI_BLANK_LINE", "")
        if example.want:
            yield "```"
            yield "```{.text .mkapi-example-output}"
            in_example = True
            yield example.want[:-1]
        if example.want or k == n - 1:
            yield "```"
            in_example = False
        lineno = example.lineno
        lineno += example.source.count("\n")
        lineno += example.want.count("\n")
        want = example.want
    if lineno < len(lines) - 1:
        if in_example:
            yield "```"
        yield from lines[lineno:]
