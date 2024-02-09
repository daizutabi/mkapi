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


FENCED_CODE = re.compile(r"^(?P<pre> *[~`]{3,}).*?^(?P=pre)\n?", re.M | re.S)


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
    text_escaped = _add_example_escape(text)
    try:
        examples = doctest.DocTestParser().get_examples(text_escaped)
    except ValueError:
        yield text
        return
    if not examples:
        yield text
        return
    lines = text_escaped.splitlines()
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


_ = r"^(?P<suffix>(?P<pre> *)(?P<prev>\S.*)\n{2,})(?P=pre) {4}\S"
FOURINDENT = re.compile(_, re.M)
DIRECTIVE = re.compile(r"^(?P<pre> *)\.\. *(?P<name>[\w\-]+):: *(?P<attr>.*)$", re.M)


def _iter_literal_block(text: str) -> Iterator[str]:
    if match := FOURINDENT.search(text):
        prefix = match.group("pre")
        indent = len(prefix)
        prev = match.group("prev")
        pos = match.start() + len(match.group("suffix"))
        if m := DIRECTIVE.match(prev):
            if m.group("name") == "code-block":
                yield text[: match.start()]
                lang = m.group("attr")
            else:
                yield text[: match.end()]
                yield from _iter_literal_block(text[match.end() :])
                return
        else:
            lang = ""
            yield text[:pos]
        code, rest = _split_block(text[pos:], indent)
        code = textwrap.indent(textwrap.dedent(code), prefix)
        yield f"{prefix}```{lang}\n{code}{prefix}```\n"
        yield from _iter_literal_block(rest)
    else:
        yield text


def _split_block(text: str, indent: int) -> tuple[str, str]:
    subs = {True: [], False: []}
    for sub, is_block in _iter_blocks(text, indent):
        subs[is_block].append(sub)
    return "".join(subs[True]), "".join(subs[False])


def _iter_blocks(text: str, indent: int) -> Iterator[tuple[str, bool]]:
    lines = text.splitlines()
    rests = []
    for k, line in enumerate(lines):
        if not line:
            rests.append("\n")
            continue
        if _get_indent(line) <= indent:
            rests.extend(f"{line}\n" for line in lines[k:])
            break
        yield "".join(rests), True
        rests.clear()
        yield f"{line}\n", True
    yield "".join(rests), False


def _get_indent(line: str) -> int:
    for k, c in enumerate(line):
        if c != " ":
            return k
    return -1


def _iter_code_blocks(text: str) -> Iterator[str]:
    for match in _iter_fenced_codes(text):
        if isinstance(match, re.Match):
            yield match.group()
        else:
            prev_type = str
            for examples in _iter_example_lists(match):
                if isinstance(examples, list):
                    if prev_type is list:
                        yield "\n"
                    yield _convert_examples(examples)
                    prev_type = list
                else:
                    yield from _iter_literal_block(examples)
                    prev_type = str


def _convert_code_block(text: str) -> str:
    return "".join(_iter_code_blocks(text))


def _replace_directive(match: re.Match) -> str:
    pre, name, attr = match.groups()
    match name:
        case "deprecated" if attr:
            if " " not in attr:
                attr = f"Deprecated since version {attr}"
            return f'{pre}!!! {name} "{attr}"'
        case "deprecated" | "warning" | "note":
            return f"{pre}!!! {name}"
        case _:
            return match.group()


INTERNAL_LINK = re.compile(r":\w+?:`(?P<name>.+?)\s+?<(?P<href>\S+?)>`")
INTERNAL_LINK_WITHOUT_HREF = re.compile(r":\w+?:`(?P<name>\S+?)`")
LINK = re.compile(r"`(?P<name>[^<].+?)\s+?<(?P<href>\S+?)>`_+", re.S)
LINK_WITHOUT_HREF = re.compile(r"`(?P<name>.+?)`_+", re.S)
REFERENCE = re.compile(r"\.\.\s+_(?P<name>.+?)(?P<sep>:\s+)(?P<href>\S+?)", re.S)


def _replace(text: str) -> str:
    """Replace link of reStructuredText."""
    text = INTERNAL_LINK.sub(r"[\g<name>][__mkapi__.\g<href>]", text)
    text = INTERNAL_LINK_WITHOUT_HREF.sub(r"[__mkapi__.\g<name>][]", text)
    text = LINK.sub(r"[\g<name>](\g<href>)", text)
    text = LINK_WITHOUT_HREF.sub(r"[\g<name>][]", text)
    text = REFERENCE.sub(r"[\g<name>]\g<sep>\g<href>", text)
    return DIRECTIVE.sub(_replace_directive, text)


def _convert(text: str) -> Iterator[str]:
    text = _convert_code_block(text)
    for match in _iter_fenced_codes(text):
        if isinstance(match, re.Match):
            yield match.group()
        else:
            yield _replace(match)


def convert(text: str) -> str:
    """Convert markdown."""
    return "".join(_convert(text))


INLINE_CODE = re.compile(r"(?P<pre>`+).+?(?P=pre)")


def finditer(pattern: re.Pattern, text: str) -> Iterator[re.Match | str]:
    """Yield strings or match objects from a markdown text."""
    for match in _iter_fenced_codes(text):
        if isinstance(match, re.Match):
            yield match.group()
        else:
            yield from _iter(pattern, match)
            # for m in _iter(INLINE_CODE, match):
            #     if isinstance(m, re.Match):
            #         yield m.group()
            #     else:


def sub(pattern: re.Pattern, rel: Callable[[re.Match], str], text: str) -> str:
    """Replace a markdown text."""
    subs = (m if isinstance(m, str) else rel(m) for m in finditer(pattern, text))
    return "".join(subs)


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
    """Return an admonition markdown for a "Notes" or "Warnings" section."""
    lines = [f'!!! {name} "{title}"']
    lines.extend("    " + line if line else "" for line in text.splitlines())
    return "\n".join(lines)
