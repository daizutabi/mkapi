"""
Provide functions for processing and converting Markdown text.

Include utilities for handling code blocks, links, and examples
within Markdown content. The functions are designed to facilitate the extraction,
transformation, and formatting of Markdown elements, making it easier to generate
well-structured documentation.

Key functionalities include:
- Iterate over matches of regex patterns in text.
- Handle fenced and inline code blocks.
- Escape and unescape specific patterns for processing.
"""

from __future__ import annotations

import doctest
import re
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def _iter(
    pattern: re.Pattern, text: str, pos: int = 0, endpos: int | None = None
) -> Iterator[re.Match[str] | tuple[int, int]]:
    """Iterate over matches of a regex pattern in the given text.

    Search for all occurrences of the specified regex pattern
    in the provided text. Yield the segments of text between matches
    as well as the matches themselves. This allows for processing
    both the matched content and the surrounding text in a single iteration.

    Args:
        pattern (re.Pattern): The compiled regex pattern to search for in the text.
        text (str): The text to search for matches.

    Yields:
        re.Match | tuple[int, int]: Segments of text and match objects. The segments
        are the parts of the text that are not matched by the pattern, and the
        matches are the regex match objects.

    Examples:
        >>> import re
        >>> pattern = re.compile(r'\\d+')
        >>> text = "There are 2 apples and 3 oranges."
        >>> matches = list(_iter(pattern, text))
        >>> matches[0]
        (0, 10)
        >>> matches[1]
        <re.Match object; span=(10, 11), match='2'>
        >>> matches[2]
        (11, 23)
        >>> matches[3]
        <re.Match object; span=(23, 24), match='3'>
        >>> matches[4]
        (24, 33)
    """
    if endpos is None:
        endpos = len(text)

    cursor = pos

    for match in pattern.finditer(text, pos, endpos=endpos):
        start, end = match.start(), match.end()

        if cursor < start:
            yield cursor, start

        yield match

        cursor = end

    if cursor < endpos:
        yield cursor, endpos


FENCED_CODE = re.compile(r"^(?P<pre> *[~`]{3,}).*?^(?P=pre)", re.M | re.S)


def _iter_fenced_codes(
    text: str, pos: int = 0, endpos: int | None = None
) -> Iterator[re.Match[str] | tuple[int, int]]:
    return _iter(FENCED_CODE, text, pos, endpos)


DOCTEST = re.compile(r" *#+ *doctest:.*$", re.M)
PROMPT_ONLY = re.compile(r"^(?P<pre> *\>\>\> *)$", re.M)
COMMENT_ONLY = re.compile(r"^(?P<pre> *\>\>\> )(?P<comment>#.*)$", re.M)


def _add_example_escape(text: str) -> str:
    """Escape specific patterns in the provided text for processing.

    Modify the input text by escaping certain patterns to prevent them from
    being processed as regular content. Specifically, replace prompt lines
    with a placeholder and comments with a special marker. The function also
    removes doctest directives from the text.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The modified text with escaped patterns.

    Examples:
        >>> text = ">>>\\n>>> print('Hello, World!')\\n>>> # This is a comment\\n"
        >>> x = _add_example_escape(text).splitlines()
        >>> x[0]
        '>>> MKAPI_BLANK_LINE'
        >>> x[1]
        ">>> print('Hello, World!')"
        >>> x[2]
        '>>> __mkapi__# This is a comment'
    """
    text = PROMPT_ONLY.sub(r"\g<pre> MKAPI_BLANK_LINE", text)
    text = COMMENT_ONLY.sub(r"\g<pre>__mkapi__\g<comment>", text)
    return DOCTEST.sub("", text)


def _delete_example_escape(text: str) -> str:
    """Remove escaped patterns from the provided text.

    Reverse the escaping applied to specific patterns in the input text.
    Remove the placeholder for blank lines and the special marker for comments
    that were added during the processing of the text.

    Args:
        text (str): The input text with escaped patterns to be removed.

    Returns:
        str: The modified text with escaped patterns removed.

    Examples:
        >>> text = " MKAPI_BLANK_LINE\\n__mkapi__# This is a comment\\n"
        >>> _delete_example_escape(text)
        ' \\n# This is a comment\\n'
    """
    text = text.replace("MKAPI_BLANK_LINE", "")
    return text.replace("__mkapi__", "")


def _iter_examples(text: str) -> Iterator[doctest.Example | str]:
    """Iterate over examples in the provided text.

    Scan the input text for examples formatted in doctest style.
    Escape specific patterns in the text to prevent them from being
    processed as regular content. Then, extract examples using the
    `doctest.DocTestParser`. Yield each example found, along
    with any text segments that are not part of the examples.

    Args:
        text (str): The input text containing examples to be processed.

    Yields:
        doctest.Example or str: Each example found in the text, or
        segments of text that are not part of any example.

    Examples:
        >>> text = ">>> print('Hello')\\n'Hello'\\n>>> print('World')\\n'World'\\n"
        >>> examples = list(_iter_examples(text))
        >>> len(examples)
        2
    """
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
    """Iterate over lists of examples in the provided text.

    Process the input text to extract groups of examples formatted
    in doctest style. Utilize the `_iter_examples` function to yield individual
    examples and organize them into lists based on their indentation levels.
    Yield lists of examples when a change in indentation is detected or
    when a non-example segment is encountered.

    Args:
        text (str): The input text containing examples to be processed.

    Yields:
        list[doctest.Example] | str: A list of examples found in the text,
        or segments of text that are not part of any example.

    Examples:
        >>> text = ">>> print('Hello')\\n'Hello'\\n>>> print('World')\\n'World'\\n"
        >>> example_lists = list(_iter_example_lists(text))
        >>> len(example_lists)
        2
        >>> example_lists[0][0].source
        "print('Hello')\\n"
        >>> example_lists[1][0].want
        "'World'\\n"
    """
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
    """Convert a list of doctest examples into Markdown format.

    Take a list of doctest examples and convert them into a
    Markdown representation suitable for documentation. Format the examples
    with appropriate code block syntax and include both the input and expected
    output where applicable.

    Args:
        examples (list[doctest.Example]): A list of doctest examples to be converted.

    Returns:
        str: The Markdown representation of the provided examples.
    """
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
    """Iterate over literal blocks in the provided text.

    Scan the input text for literal blocks that are indented
    and formatted according to specific rules. Identify blocks of code
    and yield them as formatted Markdown code blocks. The function also
    handles directives that may precede the code blocks, such as specifying
    the language for syntax highlighting.

    Args:
        text (str): The input text containing potential literal blocks.

    Yields:
        str: Each literal block formatted as a Markdown code block,
        or segments of text that are not part of any literal block.

    Examples:
        >>> text = " x\\n a\\n\\n\\n     b\\n\\n     c\\n\\nd\\n"
        >>> blocks = list(_iter_literal_block(text))
        >>> len(blocks)
        3
        >>> blocks[1]
        ' ```\\n b\\n\\n c\\n ```\\n'
    """
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
    """Split the input text into blocks based on indentation.

    Take a string of text and an indentation level, and separate the text
    into two parts: one containing the indented blocks and the other
    containing the non-indented segments. Utilize the `_iter_blocks` function
    to identify and categorize the segments based on their indentation.

    Args:
        text (str): The input text to be split into blocks.
        indent (int): The indentation level used to determine block separation.

    Returns:
        tuple[str, str]: A tuple where the first element is a string containing
        the indented blocks, and the second element is a string containing
        the non-indented segments.
    """
    subs = {True: [], False: []}

    for sub, is_block in _iter_blocks(text, indent):
        subs[is_block].append(sub)

    return "".join(subs[True]), "".join(subs[False])


def _iter_blocks(text: str, indent: int) -> Iterator[tuple[str, bool]]:
    """Iterate over blocks of text based on indentation.

    Process the input text to identify and yield blocks of
    text that are either indented or non-indented. Separate the text
    into segments based on the specified indentation level, allowing for
    the differentiation between code blocks and regular text.

    Args:
        text (str): The input text to be processed.
        indent (int): The indentation level used to determine block separation.

    Yields:
        tuple[str, bool]: A tuple where the first element is a string
        containing the block of text, and the second element is a boolean
        indicating whether the block is indented (True) or not (False).
    """
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
    """Get the indentation level of a given line.

    Calculate the number of leading spaces in the provided
    line of text. Iterate through the characters of the line until it
    encounters a non-space character, returning the index of that character
    as the indentation level. If the line consists entirely of spaces,
    return -1.

    Args:
        line (str): The line of text for which to determine the indentation.

    Returns:
        int: The number of leading spaces in the line, or -1 if the line
        is empty or contains only spaces.

    Examples:
        >>> _get_indent("    code block")
        4
        >>> _get_indent("no indent")
        0
        >>> _get_indent("      ")
        -1
        >>> _get_indent("")
        -1
    """
    for k, c in enumerate(line):
        if c != " ":
            return k

    return -1


def _iter_code_blocks(text: str) -> Iterator[str]:
    """Iterate over code blocks in the provided text.

    Scan the input text for both fenced code blocks and
    example lists. Yield each code block as a string, converting
    example lists into a Markdown format while preserving the structure
    of the text. Handle both matched code blocks and examples, ensuring
    they are processed correctly.

    Args:
        text (str): The input text containing code blocks and examples.

    Yields:
        Iterator[str]: Each code block found in the text, formatted as a
        Markdown code block.

    Examples:
        >>> text = "```\\nprint('Hello')\\n```\\n>>> print('World')\\n'World'\\n"
        >>> code_blocks = list(_iter_code_blocks(text))
        >>> len(code_blocks)
        3
    """
    for match in _iter_fenced_codes(text):
        if isinstance(match, re.Match):
            yield match.group()

        else:
            prev_type = str
            sub = text[match[0] : match[1]]
            for examples in _iter_example_lists(sub):
                if isinstance(examples, list):
                    if prev_type is list:
                        yield "\n"

                    yield _convert_examples(examples)
                    prev_type = list

                else:
                    yield from _iter_literal_block(examples)
                    prev_type = str


def convert_code_block(text: str) -> str:
    """Convert code blocks in the provided text to Markdown format.

    Process the input text to identify and convert code blocks
    into Markdown format. Handle both fenced code blocks and
    example lists, ensuring they are processed correctly.

    Args:
        text (str): The input text containing code blocks to be converted.

    Returns:
        str: The modified text with code blocks converted to Markdown format.
    """
    return "".join(_iter_code_blocks(text))


def _finditer(
    pattern: re.Pattern, text: str, pos: int = 0, endpos: int | None = None
) -> Iterator[re.Match[str] | tuple[int, int]]:
    for match in _iter_fenced_codes(text, pos, endpos):
        if isinstance(match, re.Match):
            yield match.start(), match.end()

        else:
            yield from _iter(pattern, text, match[0], match[1])


def finditer(
    pattern: re.Pattern, text: str, pos: int = 0, endpos: int | None = None
) -> Iterator[re.Match[str]]:
    """Find all matches of a regex pattern in the provided text.

    Search for all occurrences of the specified regex pattern
    in the provided text. The markdown code blocks are not processed.

    Args:
        pattern (re.Pattern): The compiled regex pattern to search for in the text.
        text (str): The text to search for matches.
        pos (int): The starting position in the text to search for matches.
        endpos (int | None): The ending position in the text to search for matches.

    Yields:
        re.Match: Each match found in the text.
    """
    for match in _finditer(pattern, text, pos, endpos):
        if isinstance(match, re.Match):
            yield match


def sub(
    pattern: re.Pattern,
    rel: Callable[[re.Match], str],
    text: str,
    pos: int = 0,
    endpos: int | None = None,
) -> str:
    """Substitute all matches of a regex pattern in the provided text.

    Replace all occurrences of the specified regex pattern in the provided
    text with the result of the provided callable. The markdown code blocks
    are not processed.

    Args:
        pattern (re.Pattern): The compiled regex pattern to search for in the text.
        rel (Callable[[re.Match], str]): A callable that takes a match object
            and returns a string.
        text (str): The text to search for matches and perform substitutions.
        pos (int): The starting position in the text to search for matches.
        endpos (int | None): The ending position in the text to search for matches.

    Returns:
        str: The modified text with all matches of the pattern replaced by the
        result of the callable.
    """
    subs = (
        text[m[0] : m[1]] if isinstance(m, tuple) else rel(m)
        for m in _finditer(pattern, text, pos, endpos)
    )
    return "".join(subs)


def create_admonition(name: str, title: str, text: str) -> str:
    """Create a formatted admonition block for Markdown.

    Create a Markdown representation of an admonition, which
    is a special block used to highlight important information, warnings,
    or notes, including a title and content.

    Args:
        name (str): The type of admonition (e.g., "note", "warning", "tip").
        title (str): The title of the admonition.
        text (str): The content of the admonition.

    Returns:
        str: A formatted string representing the admonition block in Markdown.

    Examples:
        >>> name = "warning"
        >>> title = "Caution"
        >>> text = "This is a warning message."
        >>> create_admonition(name, title, text)
        '!!! warning "Caution"\\n    This is a warning message.'
    """
    lines = [f'!!! {name} "{title}"']
    lines.extend("    " + line if line else "" for line in text.splitlines())
    return "\n".join(lines)
