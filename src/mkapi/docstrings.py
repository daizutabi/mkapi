"""Parse docstrings."""
from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import mkapi.markdown
from mkapi.items import (
    Item,
    Name,
    Section,
    Text,
    Type,
    create_admonition,
    create_assigns,
    create_parameters,
    create_raises,
    create_returns,
    iter_merged_items,
)
from mkapi.utils import get_by_name, unique_names

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import TypeAlias


Style: TypeAlias = Literal["google", "numpy"]


SPLIT_ITEM_PATTERN = re.compile(r"\n\S")
SPLIT_NAME_TYPE_TEXT_PATTERN = re.compile(r"^\s*(\S+?)\s*\((.+?)\)\s*:\s*(.*)$")


def _iter_items(text: str) -> Iterator[str]:
    """Yield items for Parameters, Attributes, Returns, or Raises sections.

    Items may include a type and/or text (description).
    """
    start = 0
    for m in SPLIT_ITEM_PATTERN.finditer(text):
        if item := text[start : m.start()].strip():
            yield item

        start = m.start()

    if item := text[start:].strip():
        yield item


def _split_item_google(lines: list[str]) -> tuple[str, str, str]:
    """Split an item into a tuple of (name, type, text) in the Google style."""
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


def _split_item_numpy(lines: list[str]) -> tuple[str, str, str]:
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
    """Split an item into a tuple of (name, type, text)."""
    lines = text.splitlines()

    if style == "google":
        return _split_item_google(lines)

    return _split_item_numpy(lines)


def split_item_without_name(text: str, style: str) -> tuple[str, str]:
    """Return a tuple of (type, text) for Returns or Yields section."""
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


TYPE_STRING_PATTERN = re.compile(r"\[__mkapi__.(\S+?)\]\[\]")


def iter_items(text: str, style: Style) -> Iterator[Item]:
    """Yield [Item] instances."""
    for item in _iter_items(text):
        name, type_, text = split_item(item, style)

        type_ = TYPE_STRING_PATTERN.sub(r"\1", type_)
        type_ = ast.Constant(type_) if type_ else None
        yield Item(Name(name), Type(type_), Text(text))


def iter_items_without_name(text: str, style: Style) -> Iterator[Item]:
    name = ""
    type_, text = split_item_without_name(text, style)

    if ":" in type_:
        name, type_ = (x.strip() for x in type_.split(":", maxsplit=1))

    type_ = ast.Constant(type_) if type_ else None
    yield Item(Name(name), Type(type_), Text(text))


SPLIT_SECTION_PATTERNS: dict[Style, re.Pattern[str]] = {
    "google": re.compile(r"\n\n\S"),
    "numpy": re.compile(r"\n\n\n\S|\n\n.+?\n[\-=]+\n"),
}


def _split_sections(text: str, style: Style) -> Iterator[str]:
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
    ("Assigns", "Assign", "Attributes", "Attribute", "Attrs", "Attr"),
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
    """Return the docstring style.

    If the style can't be determined, the current style is returned.
    """
    for names in SECTION_NAMES:
        for name in names:
            if f"\n\n{name}\n----" in text or f"\n\n{name}\n====" in text:
                CURRENT_DOCSTRING_STYLE[0] = "numpy"
                return "numpy"

    CURRENT_DOCSTRING_STYLE[0] = "google"
    return "google"


def _rename_section(section_name: str) -> str:
    for section_names in SECTION_NAMES:
        if section_name in section_names:
            return section_names[0]

    return section_name


def split_section(text: str, style: Style) -> tuple[str, str]:
    """Return a section name and its text."""
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
    """Yield (section name, text) pairs by splitting a docstring."""
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


def _create_section_with_items(name: str, text: str, style: Style) -> Section:
    if name == "Parameters":
        return create_parameters(iter_items(text, style))

    if name == "Assigns":
        return create_assigns(iter_items(text, style))

    if name == "Raises":
        return create_raises(iter_items(text, style))

    if name in ["Returns", "Yields"]:
        it = iter_items_without_name(text, style)
        return create_returns(it, name)

    raise NotImplementedError


def _create_section(name: str, text: str) -> Section:
    if name in ["Note", "Notes", "Warning", "Warnings", "See Also"]:
        return create_admonition(name, text)

    return Section(Name(name), Type(), Text(text), [])


def iter_sections(text: str, style: Style) -> Iterator[Section]:
    """Yield [Section] instances by splitting a docstring."""
    for name, text_ in _iter_sections(text, style):
        if name in ["Parameters", "Assigns", "Raises", "Returns", "Yields"]:
            yield _create_section_with_items(name, text_, style)

        else:
            yield _create_section(name, text_)


@dataclass
class Docstring(Item):
    """Docstring class."""

    sections: list[Section]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(sections={len(self.sections)})"

    def __iter__(self) -> Iterator[Name | Type | Text]:
        """Yield [Type] or [Text] instances."""
        yield from super().__iter__()
        for section in self.sections:
            yield from section


def parse(text: str | None, style: Style | None = None) -> Docstring:
    """Return a [Docstring] instance."""
    if not text:
        return Docstring(Name("Docstring"), Type(), Text(), [])

    style = style or get_style(text)

    text = mkapi.markdown.convert(text)
    text = mkapi.markdown.replace(text, ["<", ">"], ["&lt;", "&gt;"])

    sections = list(iter_sections(text, style))
    if sections and not sections[0].name.str:
        type_ = sections[0].type
        text_ = sections[0].text
        del sections[0]

    else:
        type_ = Type()
        text_ = Text()

    return Docstring(Name("Docstring"), type_, text_, sections)


def merge_sections(a: Section, b: Section) -> Section:
    """Merge two [Section] instances into one [Section] instance."""
    if a.name != b.name:
        raise ValueError
    type_ = a.type if a.type.expr else b.type
    text = Text(f"{a.text.str or ''}\n\n{b.text.str or ''}".strip())
    return Section(a.name, type_, text, list(iter_merged_items(a.items, b.items)))


def iter_merge_sections(a: list[Section], b: list[Section]) -> Iterator[Section]:
    """Yield merged [Section] instances from two lists of [Section]."""
    for name in unique_names(a, b):
        if name:
            ai, bi = get_by_name(a, name), get_by_name(b, name)
            if ai and not bi:
                yield ai
            elif not ai and bi:
                yield bi
            elif ai and bi:
                yield merge_sections(ai, bi)


def merge(a: Docstring, b: Docstring) -> Docstring:
    """Merge two [Docstring] instances into one [Docstring] instance."""
    sections: list[Section] = []
    for ai in a.sections:
        if ai.name:
            break
        sections.append(ai)
    sections.extend(iter_merge_sections(a.sections, b.sections))
    is_named_section = False
    for section in a.sections:
        if section.name:  # already collected, so skip.
            is_named_section = True
        elif is_named_section:
            sections.append(section)
    sections.extend(s for s in b.sections if not s.name)
    type_ = a.type  # if a.type.expr else b.type
    text = Text(f"{a.text.str or ''}\n\n{b.text.str or ''}".strip())
    return Docstring(Name("Docstring"), type_, text, sections)


def is_empty(doc: Docstring) -> bool:
    """Return True if a [Docstring] instance is empty."""
    if doc.text.str:
        return False
    for section in doc.sections:
        if section.text.str:
            return False
        for item in section.items:
            if item.text.str:
                return False
    return True
