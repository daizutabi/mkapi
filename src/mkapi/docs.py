from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import mkapi.markdown
from mkapi.utils import get_by_name, unique_names

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator
    from typing import TypeAlias


Style: TypeAlias = Literal["google", "numpy"]


SPLIT_ITEM_PATTERN = re.compile(r"\n\S")
SPLIT_NAME_TYPE_TEXT_PATTERN = re.compile(r"^\s*(\S+?)\s*\((.+?)\)\s*:\s*(.*)$")


def _iter_items(text: str) -> Iterator[str]:
    """Iterate over items in the provided text based on a specific pattern.

    This function scans the input text for items separated by a specific
    pattern defined by `SPLIT_ITEM_PATTERN`. It yields each item found,
    trimming whitespace from the start and end of each item.

    Args:
        text (str): The input text containing items to be iterated over.

    Yields:
        str: Each item found in the text, stripped of leading
        and trailing whitespace.

    Example:
        >>> text = "Item 1\\n a\\nItem 2\\n b\\nItem 3\\n c"
        >>> items = list(_iter_items(text))
        >>> items
        ['Item 1\\n a', 'Item 2\\n b', 'Item 3\\n c']

    This function is useful for processing structured text where items
    are delineated by specific patterns, allowing for easy extraction
    and manipulation of the individual items.
    """
    start = 0
    for m in SPLIT_ITEM_PATTERN.finditer(text):
        if item := text[start : m.start()].strip():
            yield item

        start = m.start()

    if item := text[start:].strip():
        yield item


def _split_google_style_item(lines: list[str]) -> tuple[str, str, str]:
    if m := re.match(SPLIT_NAME_TYPE_TEXT_PATTERN, lines[0]):
        name, type_, text = m.groups()

    elif ":" in lines[0]:
        name, text = lines[0].split(":", maxsplit=1)
        name = name.strip()
        text = text.strip()
        type_ = ""

    else:
        name, type_, text = lines[0], "", ""

    rest = "\n".join(lines[1:])
    rest = textwrap.dedent(rest)

    return name, type_, f"{text}\n{rest}".rstrip()


def _split_numpy_style_item(lines: list[str]) -> tuple[str, str, str]:
    """Split an item into a tuple of (name, type, text) in the NumPy style."""
    if ":" in lines[0]:
        name, type_ = lines[0].split(":", maxsplit=1)
        name = name.strip()
        type_ = type_.strip()

    else:
        name, type_ = lines[0], ""

    text = "\n".join(lines[1:])
    text = textwrap.dedent(text)

    return name, type_, text


def split_item(text: str, style: Style) -> tuple[str, str, str]:
    """Split a text item into its components based on the specified style.

    This function takes a string representing an item and a style indicator
    (either "google" or "numpy") and splits the item into a tuple containing
    the name, type, and text description. It delegates the actual splitting
    to the appropriate helper function based on the specified style.

    Args:
        text (str): The input text item to be split.
        style (Style): The style to use for splitting the item,
            either "google" or "numpy".

    Returns:
        tuple[str, str, str]: A tuple containing the name, type, and
        text description of the item.

    Example:
        >>> text = "param1 (int): The first parameter."
        >>> split_item(text, "google")
        ('param1', 'int', 'The first parameter.')

    This function is useful for processing documentation strings where items
    need to be extracted and categorized based on their formatting style.
    """
    lines = text.splitlines()

    if style == "google":
        return _split_google_style_item(lines)

    return _split_numpy_style_item(lines)


def split_item_without_name(text: str, style: str) -> tuple[str, str]:
    """Return a tuple of (type, text) for Returns or Yields section.

    This function processes the input text to extract the type and description
    for the Returns or Yields section of a docstring, based on the specified style.
    It handles both Google and NumPy styles, returning the appropriate components
    as a tuple.

    Args:
        text (str): The input text from which to extract the type and description.
        style (str): The style to use for processing the text,
            either "google" or "numpy".

    Returns:
        tuple[str, str]: A tuple containing the type and the text description.
        If the type cannot be determined, an empty string is returned as the type.

    Example:
        >>> text = "int: The return value."
        >>> split_item_without_name(text, "google")
        ('int', 'The return value.')

        >>> text = "str\\n    The output string."
        >>> split_item_without_name(text, "numpy")
        ('str', 'The output string.')

    This function is useful for extracting structured information from docstring
    sections, allowing for better documentation generation and analysis.
    """
    lines = text.splitlines()

    if style == "google" and ":" in lines[0]:
        type_, text = lines[0].split(":", maxsplit=1)
        type_ = type_.strip()
        text = text.strip(" ").rstrip()
        return type_, "\n".join([text, *lines[1:]])

    if style == "numpy" and len(lines) > 1 and lines[1].startswith(" "):
        text = textwrap.dedent("\n".join(lines[1:]))
        return lines[0], text

    return "", text


@dataclass
class Item:
    """Represents an item in a documentation string.

    This class is used to encapsulate the details of a single item found
    in a documentation string, such as a parameter, return value, or
    exception. It stores the name, type, and description of the item,
    providing a structured way to manage and access this information.

    Example:
        >>> item = Item(name="param1", type="int", text="The first parameter.")
        >>> item.name
        'param1'
        >>> item.type
        'int'
        >>> item.text
        'The first parameter.'
        >>> repr(item)
        "Item('param1')"

    This class is useful for processing and organizing documentation strings,
    allowing for easier extraction and manipulation of individual items within
    the documentation.
    """

    name: str
    """The name of the item, typically representing a parameter,
    return value, or exception."""

    type: str | ast.expr | None  # noqa: A003, RUF100
    """The type of the item, which can be a string representation of the type,
    an Abstract Syntax Tree (AST) expression, or None if the type is not specified."""

    text: str
    """A description or documentation text associated with the item."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


TYPE_STRING_PATTERN = re.compile(r"\[__mkapi__.(\S+?)\]\[\]")


def iter_items(text: str, style: Style) -> Iterator[Item]:
    """Yield [Item] instances from the provided text based on the specified style.

    This function processes the input text to extract items formatted according
    to the specified style (either "google" or "numpy"). It iterates over the
    items found in the text, splits each item into its components (name, type,
    and text), and yields instances of the Item class.

    Args:
        text (str): The input text containing items to be processed.
        style (Style): The style to use for splitting the items,
            either "google" or "numpy".

    Yields:
        Iterator[Item]: Each Item instance created from the extracted components
        of the items found in the text.

    Example:
        >>> text = "param1 (int): The first.\\nparam2 (str): The second."
        >>> items = list(iter_items(text, "google"))
        >>> len(items)
        2
        >>> items[0].name
        'param1'
        >>> items[0].type
        'int'
        >>> items[0].text
        'The first.'

    This function is useful for processing documentation strings where items
    need to be extracted and represented as structured data for further analysis
    or documentation generation.
    """
    for item in _iter_items(text):
        name, type_, text = split_item(item, style)
        type_ = TYPE_STRING_PATTERN.sub(r"\1", type_)
        yield Item(name, type_, text)


def iter_items_without_name(text: str, style: Style) -> Iterator[Item]:
    """Yield [Item] instances without a name from the provided text based on the specified style.

    This function processes the input text to extract items formatted according
    to the specified style (either "google" or "numpy") but does not include
    the name of the item in the resulting Item instances. It is particularly
    useful for sections like Returns or Yields where the name is not specified.

    Args:
        text (str): The input text containing items to be processed.
        style (Style): The style to use for processing the text,
            either "google" or "numpy".

    Yields:
        Iterator[Item]: Each Item instance created from the extracted components
        of the items found in the text, without a name.

    Example:
        >>> text = "int: The return value."
        >>> items = list(iter_items_without_name(text, "google"))
        >>> len(items)
        1
        >>> items[0].type
        'int'
        >>> items[0].text
        'The return value.'

    This function is useful for extracting structured information from docstring
    sections where the name of the item is not provided, allowing for better
    documentation generation and analysis.
    """
    name = ""
    type_, text = split_item_without_name(text, style)

    if ":" in type_:
        name, type_ = (x.strip() for x in type_.split(":", maxsplit=1))

    yield Item(name, type_, text)


SPLIT_SECTION_PATTERNS: dict[Style, re.Pattern[str]] = {
    "google": re.compile(r"\n\n\S"),
    "numpy": re.compile(r"\n\n\n\S|\n\n.+?\n[\-=]+\n"),
}


def _split_sections(text: str, style: Style) -> Iterator[str]:
    """Split the provided text into sections based on the specified style.

    This function scans the input text for section breaks and yields each
    section as a separate string. It uses a predefined pattern to identify
    the sections according to the specified style (either "google" or "numpy").
    If no section breaks are found, the entire text is yielded as a
    single section.

    Args:
        text (str): The input text to be split into sections.
        style (Style): The style to use for splitting the sections,
            either "google" or "numpy".

    Yields:
        str: Each section found in the text, stripped of leading and
        trailing whitespace.

    Example:
        >>> text = "Section 1\\nContent of section 1.\\n\\nSection 2\\nContent of section 2."
        >>> sections = list(_split_sections(text, "google"))
        >>> len(sections)
        2
        >>> sections[0]
        'Section 1\\nContent of section 1.'
        >>> sections[1]
        'Section 2\\nContent of section 2.'

    This function is useful for organizing documentation strings into manageable
    sections, allowing for easier processing and formatting of the content.
    """
    pattern = SPLIT_SECTION_PATTERNS[style]

    if not (m := re.search("\n\n", text)):
        yield text.strip()
        return

    start = m.end()
    yield text[:start].strip()

    for m in pattern.finditer(text, start):
        yield from _subsplit(text[start : m.start()].strip(), style)
        start = m.start()

    yield from _subsplit(text[start:].strip(), style)


# In Numpy style, if a section is indented, then a section break is
# created by resuming unindented text.
def _subsplit(text: str, style: Style) -> list[str]:
    if style == "google" or len(lines := text.splitlines()) < 3:  # noqa: PLR2004
        return [text]

    if not lines[2].startswith(" "):  # 2 == after '----' line.
        return [text]

    return text.split("\n\n")


SECTION_NAMES: list[tuple[str, ...]] = [
    ("Parameters", "Parameter", "Params", "Param"),
    ("Parameters", "Arguments", "Argument", "Args", "Arg"),
    ("Attributes", "Attribute", "Attrs", "Attr"),
    ("Returns", "Return"),
    ("Raises", "Raise"),
    ("Yields", "Yield"),
    ("Example",),
    ("Examples",),
    ("Warning", "Warn"),
    ("Warnings", "Warns"),
    ("Note",),
    ("Notes",),
    ("See Also", "See also"),
]

CURRENT_DOCSTRING_STYLE: list[Style] = ["google"]


def get_style(text: str) -> Style:
    """Return the docstring style based on the provided text.

    This function analyzes the input text to determine whether it follows
    the Google or NumPy style for docstrings. It checks for specific section
    headers and formatting patterns to identify the style. If the style cannot
    be determined, it defaults to returning the Google style.

    Args:
        text (str): The input text containing the docstring to be analyzed.

    Returns:
        Style: The determined style of the docstring, either "google" or "numpy".

    Example:
        >>> text = "Parameters:\\n    param1 (int): The first parameter."
        >>> get_style(text)
        'google'

        >>> text = "\\n\\nReturns\\n--------\\n    str: The output string."
        >>> get_style(text)
        'numpy'

        >>> get_style("")
        'google'

    This function is useful for ensuring that docstrings are processed
    consistently according to their formatting style, facilitating accurate
    extraction and documentation generation.
    """
    for names in SECTION_NAMES:
        for name in names:
            if f"\n\n{name}\n----" in text or f"\n\n{name}\n====" in text:
                CURRENT_DOCSTRING_STYLE[0] = "numpy"
                return "numpy"

    CURRENT_DOCSTRING_STYLE[0] = "google"
    return "google"


def _rename_section(section_name: str) -> str:
    """Rename a section based on predefined section names.

    This function checks the provided section name against a list of known
    section names. If a match is found, it returns the first name in the
    corresponding tuple of section names. If no match is found, it returns
    the original section name.

    Args:
        section_name (str): The name of the section to be renamed.

    Returns:
        str: The renamed section name if a match is found; otherwise, the
        original section name.

    Example:
        >>> _rename_section("Parameters")
        'Parameters'
        >>> _rename_section("Args")
        'Parameters'
        >>> _rename_section("Unknown Section")
        'Unknown Section'

    This function is useful for standardizing section names in documentation,
    ensuring consistency across different docstring formats.
    """
    for section_names in SECTION_NAMES:
        if section_name in section_names:
            return section_names[0]

    return section_name


def split_section(text: str, style: Style) -> tuple[str, str]:
    """Return a section name and its text based on the specified style.

    This function processes the input text to extract the section name and
    its corresponding content. It identifies the section name based on the
    formatting style (either "google" or "numpy") and returns the name
    along with the text that follows it.

    Args:
        text (str): The input text representing a section, which may include
            a section header followed by indented content.
        style (Style): The style to use for processing the section, either
            "google" or "numpy".

    Returns:
        tuple[str, str]: A tuple containing the section name and the text
        associated with that section. If the section name cannot be determined,
        an empty string is returned as the name.

    Example:
        >>> text = "Args:\\n    param1 (int): The first parameter."
        >>> split_section(text, "google")
        ('Args', 'param1 (int): The first parameter.')

        >>> text = "Returns\\n--------\\n    str: The output string."
        >>> split_section(text, "numpy")
        ('Returns', 'str: The output string.')

    This function is useful for organizing documentation strings into
    manageable sections, allowing for easier processing and formatting
    of the content.
    """
    lines = text.splitlines()
    if len(lines) < 2:  # noqa: PLR2004
        return "", text

    if style == "google" and re.match(r"^([A-Za-z0-9][^:]*):$", lines[0]):
        text = textwrap.dedent("\n".join(lines[1:]))
        return lines[0][:-1], text

    if style == "numpy" and re.match(r"^[\-=]+?$", lines[1]):
        text = textwrap.dedent("\n".join(lines[2:]))
        return lines[0], text

    return "", text


def _iter_sections(text: str, style: Style) -> Iterator[tuple[str, str]]:
    """Yield (section name, text) pairs by splitting a docstring.

    This function processes the input text to extract sections formatted according
    to the specified style (either "google" or "numpy"). It splits the text into
    sections, yielding each section's name and its corresponding content as a tuple.

    Args:
        text (str): The input text containing the docstring to be processed.
        style (Style): The style to use for splitting the sections, either "google" or "numpy".

    Yields:
        Iterator[tuple[str, str]]: Each tuple contains the section name and the text
        associated with that section. If a section has no name, an empty string is returned as the name.

    Example:
        >>> text = "Args:\\n    param1 (int): The first parameter.\\n\\n"
        >>> text += "Returns:\\n    str: The output string."
        >>> sections = list(_iter_sections(text, "google"))
        >>> len(sections)
        2
        >>> sections[0]
        ('Parameters', 'param1 (int): The first parameter.')
        >>> sections[1]
        ('Returns', 'str: The output string.')

    This function is useful for organizing documentation strings into manageable
    sections, allowing for easier processing and formatting of the content.
    """
    prev_name, prev_text = "", ""
    for section in _split_sections(text, style):
        if not section:
            continue

        name, text = split_section(section, style)
        if not text:
            continue

        name = _rename_section(name)
        if prev_name == name == "":  # successive 'plain' section.
            prev_text = f"{prev_text}\n\n{text}" if prev_text else text
            continue

        elif prev_name == "" and name != "" and prev_text:
            yield prev_name, prev_text

        yield name, text
        prev_name, prev_text = name, ""

    if prev_text:
        yield "", prev_text


@dataclass(repr=False)
class Section(Item):
    """Represents a section in a documentation string.

    This class is used to encapsulate the details of a section found in a
    documentation string. A section typically contains a name, an optional
    type, a description, and a list of items that belong to that section.
    It provides a structured way to manage and access the information related
    to a specific part of the documentation.

    Attributes:
        name (str): The name of the section, such as "Parameters", "Returns",
            or "Attributes".
        type (str): The type of the section, which can provide additional context
            about the section's content.
        text (str): A description or documentation text associated with the section.
        items (list[Item]): A list of Item instances that belong to this section,
            representing individual parameters, return values, or exceptions.

    Example:
        >>> section = Section(name="Parameters", type="", text="The parameters for the function.", items=[])
        >>> section.name
        'Parameters'
        >>> section.items
        []

    This class is useful for organizing documentation strings into manageable
    sections, allowing for easier processing and formatting of the content.
    """

    items: list[Item]
    """A list of Item instances that belong to this section,
    representing individual parameters, return values, or exceptions."""


def _create_admonition(name: str, text: str) -> str:
    """Create an admonition block based on the provided name and text.

    This function generates a formatted admonition block for documentation
    based on the type of admonition indicated by the name. It supports
    different types of admonitions such as "Note", "Warning", and "See Also".
    The function raises an error if the provided name does not match any
    known admonition types.

    Args:
        name (str): The name of the admonition, which determines its type.
        text (str): The content of the admonition, providing additional information.

    Returns:
        str: A formatted string representing the admonition block.

    Raises:
        NotImplementedError: If the provided name does not match any known
        admonition types.

    Example:
        >>> note_admonition = _create_admonition("Note", "This is a note.")
        >>> print(note_admonition)
        !!! note "Note"
            This is a note.

        >>> warning_admonition = _create_admonition("Warning", "This is a warning.")
        >>> print(warning_admonition)
        !!! warning "Warning"
            This is a warning.

    This function is useful for generating standardized admonition blocks
    in documentation, enhancing the readability and organization of the content.
    """
    if name.startswith("Note"):
        kind = "note"

    elif name.startswith("Warning"):
        kind = "warning"

    elif name.startswith("See Also"):
        kind = "info"
        text = mkapi.markdown.get_see_also(text)

    else:
        raise NotImplementedError

    return mkapi.markdown.get_admonition(kind, name, text)


def iter_sections(text: str, style: Style) -> Iterator[Section]:
    """Yield [Section] instances by splitting a docstring.

    This function processes the input text to extract sections formatted according
    to the specified style (either "google" or "numpy"). It splits the text into
    sections, yielding instances of the Section class for each identified section.
    The function handles special sections such as "Note", "Warning", and "See Also"
    by creating admonition blocks.

    Args:
        text (str): The input text containing the docstring to be processed.
        style (Style): The style to use for splitting the sections,
            either "google" or "numpy".

    Yields:
        Section: Each Section instance created from the extracted components
        of the sections found in the text.

    Example:
        >>> text = "Parameters:\\n    param1 (int): The first parameter.\\n\\n"
        >>> text += "Returns:\\n    str: The output string."
        >>> sections = list(iter_sections(text, "google"))
        >>> len(sections)
        2
        >>> sections[0].name
        'Parameters'
        >>> sections[1].name
        'Returns'

    This function is useful for organizing documentation strings into manageable
    sections, allowing for easier processing and formatting of the content.
    """
    prev_text = ""

    for name, text_ in _iter_sections(text, style):
        if name in ["", "Note", "Notes", "Warning", "Warnings", "See Also"]:
            cur_text = _create_admonition(name, text_) if name else text_
            prev_text = f"{prev_text}\n\n{cur_text}" if prev_text else cur_text
            continue

        if prev_text:
            yield Section("", "", prev_text, [])
            prev_text = ""

        if name in ["Parameters", "Attributes", "Raises"]:
            items = list(iter_items(text_, style))
            yield Section(name, "", "", items)

        elif name in ["Returns", "Yields"]:
            items = list(iter_items_without_name(text_, style))
            yield Section(name, "", "", items)

        else:
            yield Section(name, "", text_, [])

    if prev_text:
        yield Section("", "", prev_text, [])


@dataclass
class Doc(Item):
    """Represents a documentation string.

    This class encapsulates the details of a documentation string, including
    its type, text content, and the sections it contains. It provides a structured
    way to manage and access the information related to the documentation, allowing
    for easier processing and manipulation.

    Attributes:
        name (str): The name of the documentation, typically representing the
            overall subject or purpose of the docstring.
        type (str): The type of the documentation, which can provide additional
            context about the content.
        text (str): The main text content of the documentation, which may include
            introductory information or general descriptions.
        sections (list[Section]): A list of Section instances that represent
            the structured sections within the documentation, such as parameters,
            return values, and examples.

    Example:
        >>> doc = Doc(name="Doc", type="Function", text="This is a sample function.", sections=[])
        >>> doc.name
        'Doc'
        >>> doc.type
        'Function'
        >>> doc.text
        'This is a sample function.'
        >>> len(doc.sections)
        0

    This class is useful for organizing and representing documentation strings
    in a structured manner, facilitating easier extraction, formatting, and
    generation of documentation content.
    """

    sections: list[Section]
    """A list of [Section] instances that represent the structured sections
    within the documentation, such as parameters, return values, and examples."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(sections={len(self.sections)})"


def create_doc(text: str | None, style: Style | None = None) -> Doc:
    """Create and return a [Doc] instance from the provided text.

    This function takes a string representing a documentation text and an optional
    style indicator (either "google" or "numpy"). It processes the input text to
    convert it into a structured Doc instance, which includes the main text content
    and any sections extracted from the text.

    Args:
        text (str | None): The input text to be converted into a Doc instance.
            If None, an empty Doc instance is returned.
        style (Style | None): The style to use for processing the text,
            either "google" or "numpy". If not provided, the style is inferred
            from the text.

    Returns:
        Doc: A Doc instance containing the structured documentation information.

    Example:
        >>> text = "Parameters:\\n    param1 (int): The first parameter.\\n\\n"
        >>> text += "Returns:\\n    str: The output string."
        >>> doc = create_doc(text, "google")
        >>> doc.name
        'Doc'
        >>> len(doc.sections)
        2

    This function is useful for converting raw documentation strings into a
    structured format that can be easily manipulated and rendered.
    """
    if not text:
        return Doc("Doc", "", "", [])

    style = style or get_style(text)

    text = mkapi.markdown.convert(text)
    text = mkapi.markdown.replace(text, ["<", ">"], ["&lt;", "&gt;"])

    sections = list(iter_sections(text, style))

    if sections and not sections[0].name:
        type_ = sections[0].type
        text_ = sections[0].text
        del sections[0]

    else:
        type_ = ""
        text_ = ""

    return Doc("Doc", type_, text_, sections)


def create_doc_comment(text: str) -> Doc:
    """Create and return a [Doc] instance from a docstring comment.

    This function processes a string representing a documentation comment
    (typically from a Returns or Yields section) and converts it into a
    structured Doc instance. It extracts the type and text description
    from the input text and initializes a Doc instance with this information.

    Args:
        text (str): The input text representing the documentation comment
            to be converted into a Doc instance.

    Returns:
        Doc: A Doc instance containing the type and text extracted from
        the input comment, with an empty list of sections.

    Example:
        >>> doc_comment = create_doc_comment("str: The output string.")
        >>> doc_comment.name
        'Doc'
        >>> doc_comment.type
        'str'
        >>> doc_comment.text
        'The output string.'
        >>> len(doc_comment.sections)
        0

    This function is useful for converting raw documentation comments into
    a structured format that can be easily manipulated and rendered.
    """
    type_, text = split_item_without_name(text, "google")
    return Doc("Doc", type_, text, [])


def split_type(doc: Doc) -> None:
    """Split the type and text of a Doc instance.

    This function checks if the type of the provided Doc instance is not set
    and if the text is available. If both conditions are met, it extracts
    the type and text from the Doc's text using the `split_item_without_name`
    function, assuming the text follows the Google style format.

    Args:
        doc (Doc): The Doc instance whose type and text are to be split.

    Returns:
        None: This function modifies the Doc instance in place and does not return a value.

    Example:
        >>> doc = Doc(name="Doc", type="", text="str: The output string.", sections=[])
        >>> split_type(doc)
        >>> doc.type
        'str'
        >>> doc.text
        'The output string.'
    """
    if not doc.type and doc.text:
        doc.type, doc.text = split_item_without_name(doc.text, "google")


def create_summary_item(name: str, text: str, type_: str | ast.expr | None = None):
    """Create a summary item from the provided name, text, and type.

    This function generates an Item instance that represents a summary
    line extracted from the provided text. It takes the first paragraph
    of the text as the summary and associates it with the given name
    and type.

    Args:
        name (str): The name of the item, typically representing a parameter,
            return value, or other documentation element.
        text (str): The input text from which to extract the summary line.
        type_ (str | ast.expr | None): The type of the item, which can provide
            additional context about the item. This can be a string or an AST
            expression.

    Returns:
        Item: An Item instance containing the provided name, type, and the
        extracted summary line from the text.

    Example:
        >>> text = "This is a parameter.\\n\\nIt has multiple lines."
        >>> item = create_summary_item("param1", text, "str")
        >>> item.name
        'param1'
        >>> item.type
        'str'
        >>> item.text
        'This is a parameter.'

    This function is useful for creating structured representations of
    documentation elements, allowing for easier processing and rendering.
    """
    text = text.split("\n\n")[0]  # summary line
    return Item(name, type_, text)


def merge_items(a: Item, b: Item) -> Item:
    """Merge two [Item] instances into one [Item] instance.

    This function combines the attributes of two Item instances, taking
    the first item's name and the type from either item (if one is missing).
    The text from both items is concatenated with a double newline in between.

    Args:
        a (Item): The first Item instance to merge.
        b (Item): The second Item instance to merge.

    Returns:
        Item: A new Item instance containing the merged attributes from both
        input items.

    Example:
        >>> item1 = Item(name="param1", type="int", text="The first parameter.")
        >>> item2 = Item(name="param2", type="str", text="The second parameter.")
        >>> merged_item = merge_items(item1, item2)
        >>> merged_item.name
        'param1'
        >>> merged_item.type
        'int'
        >>> merged_item.text
        'The first parameter.\\n\\nThe second parameter.'

    This function is useful for consolidating information from multiple
    Item instances into a single representation, facilitating easier
    processing and rendering of documentation elements.
    """
    type_ = a.type or b.type
    text = f"{a.text}\n\n{b.text}".strip()
    return Item(a.name, type_, text)


def iter_merged_items(a: list[Item], b: list[Item]) -> Iterator[Item]:
    """Yield merged [Item] instances from two lists of [Item].

    This function takes two lists of Item instances and yields merged
    Item instances based on their names. If an Item exists in both lists,
    it merges them into a single Item. If an Item exists in only one list,
    it yields that Item as is.

    Args:
        a (list[Item]): The first list of Item instances to merge.
        b (list[Item]): The second list of Item instances to merge.

    Yields:
        Iterator[Item]: Each merged Item instance or an Item from one of the lists
        if it does not have a counterpart in the other list.

    Example:
        >>> item1 = Item(name="param1", type="int", text="The first parameter.")
        >>> item2 = Item(name="param2", type="str", text="The second parameter.")
        >>> item3 = Item(name="param1", type="float", text="Updated first parameter.")
        >>> merged_items = list(iter_merged_items([item1, item2], [item3]))
        >>> len(merged_items)
        2
        >>> merged_items[0].name
        'param1'
        >>> merged_items[1].name
        'param2'
        >>> merged_items[0].type
        'int'
        >>> merged_items[0].text
        'The first parameter.\\n\\nUpdated first parameter.'

    This function is useful for consolidating information from multiple
    Item instances across different lists, allowing for easier processing
    and rendering of documentation elements.
    """
    for name in unique_names(a, b):
        ai, bi = get_by_name(a, name), get_by_name(b, name)

        if ai and not bi:
            yield ai

        elif not ai and bi:
            yield bi

        elif ai and bi:
            yield merge_items(ai, bi)


def merge_sections(a: Section, b: Section) -> Section:
    """Merge two [Section] instances into one [Section] instance.

    This function combines the attributes of two Section instances, taking
    the first section's name and the type from either section (if one is missing).
    The text from both sections is concatenated with a double newline in between,
    and the items from both sections are merged.

    Args:
        a (Section): The first Section instance to merge.
        b (Section): The second Section instance to merge.

    Returns:
        Section: A new Section instance containing the merged attributes from both
        input sections.

    This function is useful for consolidating information from multiple
    Section instances into a single representation, facilitating easier
    processing and rendering of documentation sections.
    """
    type_ = a.type or b.type
    text = f"{a.text}\n\n{b.text}".strip()
    items = iter_merged_items(a.items, b.items)
    return Section(a.name, type_, text, list(items))


def iter_merged_sections(a: list[Section], b: list[Section]) -> Iterator[Section]:
    """Yield merged [Section] instances from two lists of [Section].

    This function takes two lists of Section instances and yields merged
    Section instances based on their names. If a Section exists in both lists,
    it merges them into a single Section. If a Section exists in only one list,
    it yields that Section as is.

    Args:
        a (list[Section]): The first list of Section instances to merge.
        b (list[Section]): The second list of Section instances to merge.

    Yields:
        Iterator[Section]: Each merged Section instance or a Section from one of the lists
        if it does not have a counterpart in the other list.

    This function is useful for consolidating information from multiple
    Section instances across different lists, allowing for easier processing
    and rendering of documentation sections.
    """
    index = 0
    for ai in a:
        index += 1
        if ai.name:
            break

        yield ai

    for name in unique_names(a, b):
        if name:
            ai, bi = get_by_name(a, name), get_by_name(b, name)
            if ai and not bi:
                yield ai

            elif not ai and bi:
                yield bi

            elif ai and bi:
                yield merge_sections(ai, bi)

    for ai in a[index + 1 :]:
        if not ai.name:
            yield ai

    for bi in b:
        if not bi.name:
            yield bi


def merge(a: Doc, b: Doc) -> Doc:
    """Merge two [Doc] instances into one [Doc] instance.

    This function combines the attributes of two Doc instances, taking
    the type from either instance (if one is missing) and concatenating
    their text content with a double newline in between. It also merges
    the sections from both Doc instances into a single list of sections.

    Args:
        a (Doc): The first Doc instance to merge.
        b (Doc): The second Doc instance to merge.

    Returns:
        Doc: A new Doc instance containing the merged attributes from both
        input Doc instances.

    This function is useful for consolidating documentation information
    from multiple Doc instances into a single representation, facilitating
    easier processing and rendering of documentation content.
    """
    type_ = a.type or b.type
    text = f"{a.text}\n\n{b.text}".strip()
    sections = iter_merged_sections(a.sections, b.sections)
    return Doc("Doc", type_, text, list(sections))


def is_empty(doc: Doc) -> bool:
    """Return True if a [Doc] instance is empty.

    This function checks whether the provided Doc instance contains any text
    or sections with text. It returns True if the Doc instance is considered
    empty, meaning it has no main text, no sections with text, and no items
    with text. Otherwise, it returns False.

    Args:
        doc (Doc): The Doc instance to check for emptiness.

    Returns:
        bool: True if the Doc instance is empty; otherwise, False.

    Example:
        >>> empty_doc = Doc("EmptyDoc", type="", text="", sections=[])
        >>> is_empty(empty_doc)
        True

        >>> non_empty_doc = Doc("NonEmptyDoc", type="func", text="text is a doc.", sections=[])
        >>> is_empty(non_empty_doc)
        False

    This function is useful for determining whether a Doc instance has any
    meaningful content, which can be important for processing and rendering
    documentation.
    """
    if doc.text:
        return False

    for section in doc.sections:
        if section.text:
            return False

        for item in section.items:
            if item.text:
                return False

    return True
