"""Markdown utility."""
from __future__ import annotations

import doctest
import re
import textwrap
from typing import TYPE_CHECKING

from mkapi.utils import iter_identifiers

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def _iter(pattern: re.Pattern, text: str) -> Iterator[re.Match | str]:
    cursor = 0
    for match in pattern.finditer(text):
        start, end = match.start(), match.end()
        if cursor < start:
            yield text[cursor:start]
        yield match
        cursor = end
    if cursor < len(text):
        yield text[cursor:]


FENCED_CODE = re.compile(r"^(?P<pre> *[~`]{3,}).*^(?P=pre)\n?", re.M | re.S)


def _iter_fenced_codes(text: str) -> Iterator[re.Match | str]:
    return _iter(FENCED_CODE, text)


DOCTEST = re.compile(r" *#+ *doctest:.*$", re.M)
PROMPT_ONLY = re.compile(r"^(?P<pre> *\>\>\> *)$", re.M)
COMMENT_ONLY = re.compile(r"^(?P<pre> *\>\>\> )(?P<comment>#.*)$", re.M)


def _add_example_escape(text: str) -> str:
    text = PROMPT_ONLY.sub(r"\g<pre> MKAPI_BLANK_LINE", text)
    text = COMMENT_ONLY.sub(r"\g<pre>__mkapi__\g<comment>", text)
    return DOCTEST.sub("", text)


def _delete_example_escape(text: str) -> str:
    text = text.replace("MKAPI_BLANK_LINE", "")
    return text.replace("__mkapi__", "")


def _iter_examples(text: str) -> Iterator[doctest.Example | str]:
    if "\n" not in text:
        yield text
        return
    text = _add_example_escape(text)
    try:
        examples = doctest.DocTestParser().get_examples(text)
    except ValueError:
        yield _delete_example_escape(text)
        return
    if not examples:
        yield _delete_example_escape(text)
        return
    lines = text.splitlines()
    current = 0
    for example in examples:
        if example.lineno > current:
            text_ = "\n".join(lines[current : example.lineno]) + "\n"
            yield _delete_example_escape(text_)
        example.source = _delete_example_escape(example.source)
        yield example
        current = example.lineno
        current += example.source.count("\n")
        current += example.want.count("\n")
    if current < len(lines) - 1:
        text_ = "\n".join(lines[current:]) + ("\n" if text.endswith("\n") else "")
        yield _delete_example_escape(text_)


def _iter_example_lists(text: str) -> Iterator[list[doctest.Example] | str]:
    examples: list[doctest.Example] = []
    for example in _iter_examples(text):
        if isinstance(example, str):
            if examples:
                yield examples
                examples = []
            yield example
        else:
            if examples and examples[-1].indent != example.indent:
                yield examples
                examples = []
            examples.append(example)
            if example.want:
                yield examples
                examples = []
    if examples:
        yield examples


def _convert_examples(examples: list[doctest.Example]) -> str:
    attr = ".python .mkapi-example-"
    prefix = " " * examples[0].indent
    lines = [f"{prefix}```{{{attr}input}}"]
    lines.extend(textwrap.indent(e.source.rstrip(), prefix) for e in examples)
    lines.append(f"{prefix}```\n")
    if want := examples[-1].want:
        want = textwrap.indent(want.rstrip(), prefix)
        output = f"{prefix}```{{{attr}output}}\n"
        output = f"{output}{want}\n{prefix}```\n"
        lines.append(output)
    return "\n".join(lines)


def _split(text: str) -> Iterator[tuple[str, bool]]:
    for match in _iter_fenced_codes(text):
        if isinstance(match, re.Match):
            yield match.group(), False
        else:
            for examples in _iter_example_lists(match):
                if isinstance(examples, list):
                    yield _convert_examples(examples), False
                else:
                    yield examples, True


def finditer(pattern: re.Pattern, text: str) -> Iterator[re.Match | str]:
    """Yield strings or match objects from a markdown text."""
    for sub, is_text in _split(text):
        if is_text:
            yield from _iter(pattern, sub)
        else:
            yield sub


def sub(pattern: re.Pattern, rel: Callable[[re.Match], str], text: str) -> str:
    """Replace a markdown text."""
    subs = (m if isinstance(m, str) else rel(m) for m in finditer(pattern, text))
    return "".join(subs)


def convert(text: str) -> str:
    """Convert markdown."""
    subs = []
    for sub, is_text in _split(text):
        if is_text:
            subs.extend(_convert_text(sub))
        else:
            subs.append(sub)
    return "".join(subs)


DIRECTIVE = re.compile(r"^(?P<pre> *).. *(?P<name>[\w\-_]+):: *(?P<attr>.*)$", re.M)


def _convert_text(text: str) -> Iterator[str]:
    it = _iter(DIRECTIVE, text)
    for m in it:
        if isinstance(m, str):
            yield _convert_inline(m)
        else:
            yield from _convert_directive(m, it)


def _convert_directive(m: re.Match, it: Iterator[re.Match | str]) -> Iterator[str]:
    prefix, name, attr = m.groups()
    match name:
        case "deprecated" if attr:
            if " " not in attr:
                attr = f"Deprecated since version {attr}"
            yield f'{prefix}!!! {name} "{attr}"'
        case "deprecated" | "warning" | "note":
            yield f"{prefix}!!! {name}"
        case "code-block":
            try:
                code = next(it)
            except StopIteration:
                code = ""
            if isinstance(code, str):
                yield from _convert_code_block(attr, prefix, code)
            else:
                yield m.group()
                yield code.group()
        case _:
            yield m.group()


def _convert_code_block(lang: str, prefix: str, code: str) -> Iterator[str]:
    yield f"{prefix}```{lang}"
    indent = -1
    lines = code.splitlines()
    rests = []
    for k, line in enumerate(lines):
        if not line:
            rests.append("\n")
            continue
        current_indent = _get_indent(line)
        if indent == -1:
            indent = current_indent
        elif current_indent < indent:
            rests.extend(f"{line}\n" for line in lines[k:])
            break
        yield from rests
        rests.clear()
        yield f"{prefix}{line[indent:]}\n"
    yield f"{prefix}```\n"
    yield _convert_inline("".join(rests))


def _get_indent(line: str) -> int:
    for k, c in enumerate(line):
        if c != " ":
            return k
    return -1


def _convert_inline(text: str) -> str:
    # return text
    return replace_link(text)


INTERNAL_LINK_PATTERN = re.compile(r":\w+?:`(?P<name>.+?)\s+?<(?P<href>\S+?)>`")
INTERNAL_LINK_WITHOUT_HREF_PATTERN = re.compile(r":\w+?:`(?P<name>\S+?)`")
LINK_PATTERN = re.compile(r"`(?P<name>[^<].+?)\s+?<(?P<href>\S+?)>`_+", re.DOTALL)
LINK_WITHOUT_HREF_PATTERN = re.compile(r"`(?P<name>.+?)`_+", re.DOTALL)
_ = r"..\s+_(?P<name>.+?)(?P<sep>:\s+)(?P<href>\S+?)"
REFERENCE_PATTERN = re.compile(_, re.DOTALL)


def replace_link(text: str) -> str:
    """Replace link of reStructuredText."""
    text = re.sub(INTERNAL_LINK_PATTERN, r"[\g<name>][__mkapi__.\g<href>]", text)
    text = re.sub(INTERNAL_LINK_WITHOUT_HREF_PATTERN, r"[__mkapi__.\g<name>][]", text)
    text = re.sub(LINK_PATTERN, r"[\g<name>](\g<href>)", text)
    text = re.sub(LINK_WITHOUT_HREF_PATTERN, r"[\g<name>][]", text)
    text = re.sub(REFERENCE_PATTERN, r"[\g<name>]\g<sep>\g<href>", text)
    return text


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
    """Return an admonition markdown for a Notes or Warnings section."""
    lines = [f'!!! {name} "{title}"']
    lines.extend("    " + line if line else "" for line in text.splitlines())
    return "\n".join(lines)
