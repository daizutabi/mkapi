"""Parse docstrings."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from mkapi.elements import Text, Type
from mkapi.utils import (
    add_admonition,
    add_fence,
    get_by_name,
    join_without_first_indent,
    unique_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


type Style = Literal["google", "numpy"]


@dataclass
class Item:
    """Item class for section items."""

    name: str
    type: Type  # noqa: A003
    text: Text

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}:{self.type})"


SPLIT_ITEM_PATTERN = re.compile(r"\n\S")
SPLIT_NAME_TYPE_TEXT_PATTERN = re.compile(r"^\s*(\S+?)\s*\((.+?)\)\s*:\s*(.*)$")


def _iter_items(section: str) -> Iterator[str]:
    """Yield items for Parameters, Attributes, Returns, or Raises sections.

    Items may include a type and/or text (description).
    """
    start = 0
    for m in SPLIT_ITEM_PATTERN.finditer(section):
        yield section[start : m.start()].strip()
        start = m.start()
    yield section[start:].strip()


def _split_item_google(lines: list[str]) -> tuple[str, str, str]:
    """Split an item into a tuple of (name, type, text) in the Google style."""
    if m := re.match(SPLIT_NAME_TYPE_TEXT_PATTERN, lines[0]):
        name, type_, text = m.groups()
    elif ":" in lines[0]:
        name, text = lines[0].split(":", maxsplit=1)
        type_ = ""
    else:
        name, type_, text = lines[0], "", ""
    return name, type_, "\n".join([text.strip(), *lines[1:]])


def _split_item_numpy(lines: list[str]) -> tuple[str, str, str]:
    """Split an item into a tuple of (name, type, text) in the NumPy style."""
    if ":" in lines[0]:
        name, type_ = lines[0].split(":", maxsplit=1)
    else:
        name, type_ = lines[0], ""
    return name.strip(), type_.strip(), "\n".join(lines[1:])


def split_item(item: str, style: Style) -> tuple[str, str, str]:
    """Split an item into a tuple of (name, type, text)."""
    lines = [line.strip() for line in item.split("\n")]
    if style == "google":
        return _split_item_google(lines)
    return _split_item_numpy(lines)


def iter_items(section: str, style: Style, section_name: str) -> Iterator[Item]:
    """Yield [Item] instances.

    If the section name is 'Raises', the type is set by its name.
    """
    for item in _iter_items(section):
        name, type_, text = split_item(item, style)
        name = name.replace("*", "")  # *args -> args, **kwargs -> kwargs
        if section_name == "Raises":
            type_ = name
        yield Item(name, Type(ast.Constant(type_)), Text(text))


@dataclass
class Section(Item):
    """Section class of docstring."""

    items: list[Item]

    def __iter__(self) -> Iterator[Item]:
        return iter(self.items)

    def get(self, name: str) -> Item | None:
        """Return an [Item] instance by name."""
        return get_by_name(self.items, name)


SPLIT_SECTION_PATTERNS: dict[Style, re.Pattern[str]] = {
    "google": re.compile(r"\n\n\S"),
    "numpy": re.compile(r"\n\n\n|\n\n.+?\n-+\n"),
}


def _split_sections(doc: str, style: Style) -> Iterator[str]:
    pattern = SPLIT_SECTION_PATTERNS[style]
    if not (m := re.search("\n\n", doc)):
        yield doc.strip()
        return
    start = m.end()
    yield doc[:start].strip()
    for m in pattern.finditer(doc, start):
        yield from _subsplit(doc[start : m.start()].strip(), style)
        start = m.start()
    yield from _subsplit(doc[start:].strip(), style)


# In Numpy style, if a section is indented, then a section break is
# created by resuming unindented text.
def _subsplit(doc: str, style: Style) -> list[str]:
    if style == "google" or len(lines := doc.split("\n")) < 3:
        return [doc]
    if not lines[2].startswith(" "):  # 2 == after '----' line.
        return [doc]
    return doc.split("\n\n")


SECTION_NAMES: list[tuple[str, ...]] = [
    ("Parameters", "Parameter", "Params", "Param"),
    ("Parameters", "Arguments", "Argument", "Args", "Arg"),
    ("Attributes", "Attribute", "Attrs", "Attr"),
    ("Examples", "Example"),
    ("Returns", "Return"),
    ("Raises", "Raise"),
    ("Yields", "Yield"),
    ("Warning", "Warn"),
    ("Warnings", "Warns"),
    ("Note",),
    ("Notes",),
]

CURRENT_DOCSTRING_STYLE: list[Style] = ["google"]


def get_style(doc: str) -> Style:
    """Return the docstring style.

    If the style can't be determined, the current style is returned.
    """
    for names in SECTION_NAMES:
        for name in names:
            if f"\n\n{name}\n----" in doc:
                CURRENT_DOCSTRING_STYLE[0] = "numpy"
                return "numpy"
    CURRENT_DOCSTRING_STYLE[0] = "google"
    return "google"


def _rename_section(section_name: str) -> str:
    for section_names in SECTION_NAMES:
        if section_name in section_names:
            return section_names[0]
    return section_name


def split_section(section: str, style: Style) -> tuple[str, str]:
    """Return a section name and its text."""
    lines = section.split("\n")
    if len(lines) < 2:
        return "", section
    if style == "google" and re.match(r"^([A-Za-z0-9][^:]*):$", lines[0]):
        return lines[0][:-1], join_without_first_indent(lines[1:])
    if style == "numpy" and re.match(r"^-+?$", lines[1]):
        return lines[0], join_without_first_indent(lines[2:])
    return "", section


def _iter_sections(doc: str, style: Style) -> Iterator[tuple[str, str]]:
    """Yield (section name, text) pairs by splitting a docstring."""
    prev_name, prev_text = "", ""
    for section in _split_sections(doc, style):
        if not section:
            continue
        name, text = split_section(section, style)
        if not text:
            continue
        name = _rename_section(name)
        if prev_name == name == "":  # continuous 'plain' section.
            prev_text = f"{prev_text}\n\n{text}" if prev_text else text
            continue
        elif prev_name == "" and name != "" and prev_text:
            yield prev_name, prev_text
        yield name, text
        prev_name, prev_text = name, ""
    if prev_text:
        yield "", prev_text


def split_without_name(text: str, style: Style) -> tuple[str, str]:
    """Return a tuple of (type, text) for Returns or Yields section."""
    lines = text.split("\n")
    if style == "google" and ":" in lines[0]:
        type_, text_ = lines[0].split(":", maxsplit=1)
        return type_.strip(), "\n".join([text_.strip(), *lines[1:]])
    if style == "numpy" and len(lines) > 1 and lines[1].startswith(" "):
        return lines[0], join_without_first_indent(lines[1:])
    return "", text


def iter_sections(doc: str, style: Style) -> Iterator[Section]:
    """Yield [Section] instances by splitting a docstring."""
    for name, text in _iter_sections(doc, style):
        type_, text_, items = Type(None), Text(None), []
        if name in ["Parameters", "Attributes", "Raises"]:
            items = list(iter_items(text, style, name))
        elif name in ["Returns", "Yields"]:
            type_, text_ = split_without_name(text, style)
            type_ = Type(ast.Constant(type_) if type_ else None)
            text_ = Text(text_ or None)
            items = [Item("", type_, text_)]
        elif name in ["Note", "Notes", "Warning", "Warnings"]:
            text_ = Text(add_admonition(name, text))
        else:
            text_ = Text(text)
        yield Section(name, type_, text_, items)


@dataclass(repr=False)
class Docstring(Item):
    """Docstring class."""

    sections: list[Section]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(num_sections={len(self.sections)})"

    def __iter__(self) -> Iterator[Section]:
        return iter(self.sections)

    def get(self, name: str) -> Section | None:
        """Return a [Section] by name."""
        return get_by_name(self.sections, name)


def parse(doc: str, style: Style | None = None) -> Docstring:
    """Return a [Docstring] instance."""
    doc = add_fence(doc)
    style = style or get_style(doc)
    sections = list(iter_sections(doc, style))
    if sections and not sections[0].name and (text := sections[0].text.str):
        if "\n\n" not in text:
            del sections[0]
        else:
            text, rest = text.split("\n\n", maxsplit=1)
            sections[0].text.str = rest
        text = Text(text)
    else:
        text = Text(None)
    return Docstring("", Type(None), text, sections)


def iter_merged_items(a: list[Item], b: list[Item]) -> Iterator[Item]:
    """Yield merged [Item] instances from two lists of [Item]."""
    for name in unique_names(a, b):
        ai, bi = get_by_name(a, name), get_by_name(b, name)
        if ai and not bi:
            yield ai
        elif not ai and bi:
            yield bi
        elif ai and bi:
            name_ = ai.name or bi.name
            type_ = ai.type if ai.type.expr else bi.type
            text = ai.text if ai.text.str else bi.text
            yield Item(name_, type_, text)


def merge_sections(a: Section, b: Section) -> Section:
    """Merge two [Section] instances into one [Section] instance."""
    if a.name != b.name:
        raise ValueError
    type_ = a.type if a.type.expr else b.type
    text = Text(f"{a.text.str}\n\n{b.text.str}".strip())
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


def merge(a: Docstring | None, b: Docstring | None) -> Docstring | None:
    """Merge two [Docstring] instances into one [Docstring] instance."""
    if not a or not a.sections:
        return b
    if not b or not b.sections:
        return a
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
    name_ = a.name or b.name
    type_ = a.type or b.type
    text = a.text or b.text
    return Docstring(name_, type_, text, sections)
