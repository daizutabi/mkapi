"""Markdown utility."""
from __future__ import annotations

import doctest
import re
import textwrap
from typing import TYPE_CHECKING

from mkapi.utils import iter_identifiers

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def add_link(text: str) -> str:
    """Add link for a "See Also" section."""
    if "\n" in text:
        text = re.sub(r"\n\s+", " ", text)
        text = textwrap.indent(text, "* ")
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


def get_admonition(name: str, title: str, text: str) -> str:
    """Return an admonition markdown."""
    lines = [f'!!! {name} "{title}"']
    lines.extend("    " + line if line else "" for line in text.splitlines())
    return "\n".join(lines)


LINK_PATTERN = re.compile(r"`(.+?)\s+?<(\S+?)>`_+")
INTERNAL_LINK_PATTERN = re.compile(r":\S+?:`(.+?)\s+?<(\S+?)>`")
REFERENCE_PATTERN = re.compile(r":\S+?:`(\S+?)`")


def replace_link(text: str) -> str:
    """Replace link of reStructuredText."""
    text = re.sub(LINK_PATTERN, r"[\1](\2)", text)
    text = re.sub(INTERNAL_LINK_PATTERN, r"[\1][__mkapi__.\2]", text)
    return re.sub(REFERENCE_PATTERN, r"[__mkapi__.\1][]", text)


def convert(text: str) -> str:
    """Convert markdown."""
    text = replace_link(text)
    if "\n" not in text:
        return text
    text = replace_examples(text)
    return replace_directives(text)


DOCTEST_PATTERN = re.compile(r"\s*?#\s*?doctest:.*?$", re.MULTILINE)
PROMPT_ONLY = re.compile(r"\>\>\>\s*?$", re.MULTILINE)
COMMENT_ONLY = re.compile(r"\>\>\> (#.*?)$", re.MULTILINE)


def replace_examples(text: str) -> str:
    """Replace examples with fenced code."""
    if "\n" not in text:
        return text
    text_ = PROMPT_ONLY.sub(">>> MKAPI_BLANK_LINE", text)
    text_ = COMMENT_ONLY.sub(r">>> __mkapi__\1", text_)
    text_ = DOCTEST_PATTERN.sub("", text_)
    try:
        examples = doctest.DocTestParser().get_examples(text_)
    except ValueError:
        return text
    if not examples:
        return text
    return "\n".join(_iter_examples(text_, examples))


def _iter_examples(text: str, examples: list[doctest.Example]) -> Iterator[str]:
    n = len(examples)
    lines = text.splitlines()
    lineno = 0
    want = "dummy"
    prefix = ""
    in_example = False
    for k, example in enumerate(examples):
        if example.lineno > lineno:
            if in_example:
                yield f"{prefix}```"
                # yield f"{prefix}</div>"
                in_example = False
            yield "\n".join(lines[lineno : example.lineno])
        if want or not in_example:
            prefix = " " * example.indent
            in_example = True
            # yield f'{prefix}<div class="mkapi-example" mkarkdown="1">'
            yield f"{prefix}```{{.python .mkapi-example-input}}"
        source = example.source[:-1].replace("MKAPI_BLANK_LINE", "")
        source = source.replace("__mkapi__", "")
        yield textwrap.indent(source, prefix)
        if example.want:
            yield f"{prefix}```"
            yield f"{prefix}```{{.text .mkapi-example-output}}"
            yield textwrap.indent(example.want[:-1], prefix)
        if example.want or k == n - 1:
            yield f"{prefix}```"
            # yield f"{prefix}</div>"
            in_example = False
        lineno = example.lineno
        lineno += example.source.count("\n")
        lineno += example.want.count("\n")
        want = example.want
    if lineno < len(lines) - 1:
        if in_example:
            yield f"{prefix}```"
            # yield f"{prefix}</div>"
        yield "\n".join(lines[lineno:])


def replace_directives(text: str) -> str:
    """Replace directives with admonition or fenced code."""
    if "\n" not in text:
        return text
    return "\n".join(_iter_directives(text))


DIRECTIVE_PATTERN = re.compile(r"(^\s*?).. (\S+?)::\s*?(\S*?)$", re.MULTILINE)


def _iter_directives(text: str) -> Iterator[str]:
    lines = text.splitlines()
    name = ""
    title = ""
    it = iter(lines)
    for line in it:
        if match := DIRECTIVE_PATTERN.match(line):
            prefix, name, suffix = match.groups()
            if name == "deprecated" and suffix:
                title = f"Deprecated since version {suffix.strip()}"
                yield f'{prefix}!!! {name} "{title}"'
            elif name in ["deprecated", "warning", "note"]:
                yield f"{prefix}!!! {name}"
            elif name == "code-block":
                # yield f"{prefix}!!! {name}"
                yield from _iter_code_block(it, suffix.strip())
        else:
            yield line


def _get_indent(line: str) -> int:
    for k, c in enumerate(line):
        if c != " ":
            return k
    return -1


def _iter_code_block(it: Iterable[str], lang: str) -> Iterator[str]:
    codes = []
    indent = -1
    for code in it:
        if not (blank := code.strip()):
            if not codes:
                yield blank
            else:
                codes.append(blank)
        if code:
            current_indent = _get_indent(code)
            if not codes:
                indent = current_indent
                codes.append(code)
            elif current_indent >= indent:
                codes.append(code)
            else:
                yield from _get_code_block(codes, lang, indent)
                yield code
                return
    yield from _get_code_block(codes, lang, indent)


def _get_code_block(codes: list[str], lang: str, indent: int) -> Iterator[str]:  # noqa: ARG001
    prefix = " " * indent  # noqa: F841
    # yield f"{prefix}```{{.{lang} .mkapi-example}}"
    # yield f"{prefix}~~~{lang}"
    for stop in range(len(codes) - 1, 0, -1):
        if codes[stop]:
            break
    for k in range(stop + 1):
        yield codes[k]
    # yield f"{prefix}```"
    # yield f"{prefix}~~~"
    for k in range(stop + 1, len(codes)):
        yield codes[k]
