"""
This module provides functions for processing and converting Markdown text.

It includes utilities for handling code blocks, links, directives, and examples
within Markdown content. The functions are designed to facilitate the extraction,
transformation, and formatting of Markdown elements, making it easier to generate
well-structured documentation.

Key functionalities include:
- Iterating over matches of regex patterns in text.
- Handling fenced and inline code blocks.
- Escaping and unescaping specific patterns for processing.
- Generating 'See Also' sections and admonition blocks.
- Replacing links and directives with their Markdown equivalents.

This module is intended for use in documentation generation and text processing
tasks where Markdown formatting is required.
"""

from __future__ import annotations

import doctest
import re
import textwrap
from typing import TYPE_CHECKING

from mkapi.utils import iter_identifiers

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def _iter(pattern: re.Pattern, text: str) -> Iterator[re.Match | str]:
    """Iterate over matches of a regex pattern in the given text.

    This function searches for all occurrences of the specified regex pattern
    in the provided text. It yields the segments of text between matches as well
    as the matches themselves. This allows for processing both the matched
    content and the surrounding text in a single iteration.

    Args:
        pattern (re.Pattern): The compiled regex pattern to search for in the text.
        text (str): The text to search for matches.

    Yields:
        re.Match | str: Segments of text and match objects. The segments
        are the parts of the text that are not matched by the pattern, and the
        matches are the regex match objects.

    Examples:
        >>> import re
        >>> pattern = re.compile(r'\\d+')
        >>> text = "There are 2 apples and 3 oranges."
        >>> matches = list(_iter(pattern, text))
        >>> matches[0]
        'There are '
        >>> matches[1]
        <re.Match object; span=(10, 11), match='2'>
        >>> matches[2]
        ' apples and '
        >>> matches[3]
        <re.Match object; span=(23, 24), match='3'>
        >>> matches[4]
        ' oranges.'

    This function is useful for processing text where both the matched patterns
    and the surrounding text need to be handled, such as in text formatting or
    transformation tasks.
    """
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
INLINE_CODE = re.compile(r"(?P<pre>`+).+?(?P=pre)")


def _iter_fenced_codes(text: str) -> Iterator[re.Match | str]:
    return _iter(FENCED_CODE, text)


DOCTEST = re.compile(r" *#+ *doctest:.*$", re.M)
PROMPT_ONLY = re.compile(r"^(?P<pre> *\>\>\> *)$", re.M)
COMMENT_ONLY = re.compile(r"^(?P<pre> *\>\>\> )(?P<comment>#.*)$", re.M)


def _add_example_escape(text: str) -> str:
    """Escape specific patterns in the provided text for processing.

    This function modifies the input text by escaping certain patterns to
    prevent them from being processed as regular content. It specifically
    replaces prompt lines with a placeholder and comments with a special
    marker. The function also removes doctest directives from the text.

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

    This function is useful for preparing text for further processing,
    particularly in scenarios where certain patterns need to be handled
    differently, such as in documentation generation or code analysis.
    """
    text = PROMPT_ONLY.sub(r"\g<pre> MKAPI_BLANK_LINE", text)
    text = COMMENT_ONLY.sub(r"\g<pre>__mkapi__\g<comment>", text)
    return DOCTEST.sub("", text)


def _delete_example_escape(text: str) -> str:
    """Remove escaped patterns from the provided text.

        This function reverses the escaping applied to specific patterns in the
        input text. It removes the placeholder for blank lines and the special
        marker for comments that were added during the processing of the text.

        Args:
            text (str): The input text with escaped patterns to be removed.

        Returns:
            str: The modified text with escaped patterns removed.

        Examples:
            >>> text = " MKAPI_BLANK_LINE\\n__mkapi__# This is a comment\\n"
            >>> _delete_example_escape(text)
            ' \\n# This is a comment\\n'

    This function is useful for restoring the original content of the text
        after processing, particularly in scenarios where the text needs to be
        returned to its original form for further use or display.
    """
    text = text.replace("MKAPI_BLANK_LINE", "")
    return text.replace("__mkapi__", "")


def _iter_examples(text: str) -> Iterator[doctest.Example | str]:
    """Iterate over examples in the provided text.

    This function scans the input text for examples formatted in doctest style.
    It first escapes specific patterns in the text to prevent them from being
    processed as regular content. Then, it extracts examples using the
    `doctest.DocTestParser`. The function yields each example found, along
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

    This function is useful for processing documentation strings that contain
    examples, allowing for the extraction and manipulation of those examples
    for further analysis or transformation.
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

    This function processes the input text to extract groups of examples formatted
    in doctest style. It utilizes the `_iter_examples` function to yield individual
    examples and organizes them into lists based on their indentation levels. The
    function yields lists of examples when a change in indentation is detected or
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

    This function is useful for organizing examples into coherent groups,
    facilitating further analysis or transformation of the examples for
    documentation or testing purposes.
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

    This function takes a list of doctest examples and converts them into a
    Markdown representation suitable for documentation. It formats the examples
    with appropriate code block syntax and includes both the input and expected
    output where applicable.

    Args:
        examples (list[doctest.Example]): A list of doctest examples to be converted.

    Returns:
        str: The Markdown representation of the provided examples.

    This function is useful for generating Markdown documentation that includes
    code examples, allowing for better readability and presentation of code
    snippets in documentation.
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

    This function scans the input text for literal blocks that are indented
    and formatted according to specific rules. It identifies blocks of code
    and yields them as formatted Markdown code blocks. The function also
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

    This function is useful for processing text where code blocks need to be
    extracted and formatted for Markdown documentation, allowing for better
    readability and presentation of code snippets.
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

    This function takes a string of text and an indentation level, and it
    separates the text into two parts: one containing the indented blocks
    and the other containing the non-indented segments. It utilizes the
    `_iter_blocks` function to identify and categorize the segments based
    on their indentation.

    Args:
        text (str): The input text to be split into blocks.
        indent (int): The indentation level used to determine block separation.

    Returns:
        tuple[str, str]: A tuple where the first element is a string containing
        the indented blocks, and the second element is a string containing
        the non-indented segments.

    This function is useful for processing text where specific indentation
    levels indicate different types of content, such as code blocks in
    Markdown documentation.
    """
    subs = {True: [], False: []}

    for sub, is_block in _iter_blocks(text, indent):
        subs[is_block].append(sub)

    return "".join(subs[True]), "".join(subs[False])


def _iter_blocks(text: str, indent: int) -> Iterator[tuple[str, bool]]:
    """Iterate over blocks of text based on indentation.

    This function processes the input text to identify and yield blocks of
    text that are either indented or non-indented. It separates the text
    into segments based on the specified indentation level, allowing for
    the differentiation between code blocks and regular text.

    Args:
        text (str): The input text to be processed.
        indent (int): The indentation level used to determine block separation.

    Yields:
        tuple[str, bool]: A tuple where the first element is a string
        containing the block of text, and the second element is a boolean indicating
        whether the block is indented (True) or not (False).

    This function is useful for processing text where indentation indicates
    different types of content, such as distinguishing between code blocks
    and regular text in Markdown documentation.
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

    This function calculates the number of leading spaces in the provided
    line of text. It iterates through the characters of the line until it
    encounters a non-space character, returning the index of that character
    as the indentation level. If the line consists entirely of spaces, it
    returns -1.

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

    This function is useful for analyzing the structure of text, particularly
    in contexts where indentation is significant, such as in code or
    Markdown documentation.
    """
    for k, c in enumerate(line):
        if c != " ":
            return k

    return -1


def _iter_code_blocks(text: str) -> Iterator[str]:
    """Iterate over code blocks in the provided text.

    This function scans the input text for both fenced code blocks and
    example lists. It yields each code block as a string, converting
    example lists into a Markdown format while preserving the structure
    of the text. The function handles both matched code blocks and
    examples, ensuring that they are processed correctly.

    Args:
        text (str): The input text containing code blocks and examples.

    Yields:
        Iterator[str]: Each code block found in the text, formatted as a
        Markdown code block.

    Examples:
        >>> text = "```\\nprint('Hello')\\n```\\n>>> print('World')\\n'World'\\n"
        >>> code_blocks = list(_iter_code_blocks(text))
        >>> len(code_blocks)
        2

    This function is useful for extracting and formatting code blocks
    from documentation or text files, allowing for better readability
    and presentation in Markdown format.
    """
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
    """Replace directives in the matched text with appropriate Markdown syntax.

    This function takes a regex match object and replaces specific directives
    (such as "deprecated", "warning", and "note") with their corresponding
    Markdown representations. It formats the output based on the directive's
    attributes, allowing for additional context to be included when necessary.

    Args:
        match (re.Match): The regex match object containing the directive
        and its attributes.

    Returns:
        str: The modified string with the directive replaced by its Markdown
        equivalent.

    This function is useful for converting documentation directives into
    a format that is compatible with Markdown, enhancing the readability
    and presentation of documentation.
    """
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
    """Replace various link and directive patterns in the text with Markdown syntax.

    This function processes the input text to convert specific patterns,
    such as internal links, external links, and directives, into their
    corresponding Markdown representations. It uses regular expressions
    to identify and replace these patterns, ensuring that the output
    text is formatted correctly for Markdown.

    Args:
        text (str): The input text containing links and directives to be replaced.

    Returns:
        str: The modified text with links and directives replaced by their
        Markdown equivalents.

    This function is useful for preparing text for Markdown documentation,
    allowing for better readability and presentation of links and directives.
    """
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
    """Convert markdown text to a processed format.

    This function takes a Markdown formatted string as input and processes it
    to convert various elements such as code blocks, links, and directives into
    a standardized format suitable for further use or output. The function
    utilizes internal conversion functions to handle specific Markdown features.

    Args:
        text (str): The Markdown text to be converted.

    Returns:
        str: The processed text after conversion.

    This function is useful for transforming Markdown content into a format
    that can be easily rendered or further manipulated in documentation tools.
    """
    return "".join(_convert(text))


def finditer(pattern: re.Pattern, text: str) -> Iterator[re.Match | str]:
    """Find and iterate over matches of a regex pattern in fenced code blocks.

    This function scans the provided text for fenced code blocks and applies
    the specified regex pattern to each block. It yields matches found in the
    code blocks as well as any matches found in the surrounding text.

    Args:
        pattern (re.Pattern): The compiled regex pattern to search for in the text.
        text (str): The text containing fenced code blocks to search.

    Yields:
        re.Match | str: Each match found in the text, either as a
        regex match object or as segments of text that are not matched by the pattern.

    This function is useful for extracting specific patterns from code blocks
    in Markdown text, allowing for further analysis or processing of the matched content.
    """
    for match in _iter_fenced_codes(text):
        if isinstance(match, re.Match):
            yield match.group()

        else:
            yield from _iter(pattern, match)


def sub(pattern: re.Pattern, rel: Callable[[re.Match], str], text: str) -> str:
    """Substitute matches of a regex pattern in the text using a replacement function.

    This function finds all matches of the specified regex pattern in the input text
    and applies a replacement function to each match. The results are then concatenated
    into a single string.

    Args:
        pattern (re.Pattern): The compiled regex pattern to search for in the text.
        rel (Callable[[re.Match], str]): A function that takes a regex match object
            and returns a string to replace the match.
        text (str): The input text in which to perform the substitutions.

    Returns:
        str: The modified text with matches replaced by the results of the replacement function.

    This function is useful for performing complex substitutions in text based on regex matches,
    allowing for dynamic modifications of the content.
    """
    subs = (m if isinstance(m, str) else rel(m) for m in finditer(pattern, text))
    return "".join(subs)


def replace(text: str, olds: list[str], news: list[str]) -> str:
    """Replace occurrences of specified substrings in the text.

    This function takes an input text and replaces occurrences of specified
    old substrings with new substrings. It processes the text by iterating
    over fenced code blocks and applying the replacements only to the non-code
    segments.

    Args:
        text (str): The input text in which to perform the replacements.
        olds (list[str]): A list of substrings to be replaced.
        news (list[str]): A list of substrings to replace the old substrings with.

    Returns:
        str: The modified text with specified substrings replaced.

    This function is useful for performing batch replacements in text, particularly
    in scenarios where certain patterns need to be updated or modified.
    """

    def _replace() -> Iterator[str]:
        for match in _iter_fenced_codes(text):
            if isinstance(match, re.Match):
                yield match.group()

            else:
                text_ = match
                for old, new in zip(olds, news, strict=True):
                    text_ = text_.replace(old, new)

                yield text_

    return "".join(_replace())


def get_see_also(text: str) -> str:
    """Generate a 'See Also' section from the provided text.

    This function processes the input text to create a formatted 'See Also'
    section. It identifies identifiers within the text and formats them as
    Markdown links. If the text contains newlines, it replaces them with spaces
    and prefixes each line with an asterisk for bullet point formatting.

    Args:
        text (str): The input text from which to generate the 'See Also' section.

    Returns:
        str: A formatted string representing the 'See Also' section with Markdown links.

    This function is useful for creating references to related content in documentation,
    enhancing the navigability and usability of the documentation.
    """
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
    """Generate a formatted admonition block for Markdown.

    This function creates a Markdown representation of an admonition, which
    is a special block used to highlight important information, warnings,
    or notes. The function formats the admonition with a specified name,
    title, and content.

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
        >>> get_admonition(name, title, text)
        '!!! warning "Caution"\\n    This is a warning message.'

    This function is useful for creating visually distinct sections in
    documentation that draw attention to important information.
    """
    lines = [f'!!! {name} "{title}"']
    lines.extend("    " + line if line else "" for line in text.splitlines())
    return "\n".join(lines)
