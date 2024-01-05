"""Parse docstrings."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

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
class Item:  # noqa: D101
    name: str
    type: str  # noqa: A003
    description: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}:{self.type})"


SPLIT_ITEM_PATTERN = re.compile(r"\n\S")
SPLIT_NAME_TYPE_DESC_PATTERN = re.compile(r"^\s*(\S+?)\s*\((.+?)\)\s*:\s*(.*)$")


def _iter_items(section: str) -> Iterator[str]:
    """Yield items for Parameters, Attributes, and Raises sections."""
    start = 0
    for m in SPLIT_ITEM_PATTERN.finditer(section):
        yield section[start : m.start()].strip()
        start = m.start()
    yield section[start:].strip()


def _split_item_google(lines: list[str]) -> tuple[str, str, str]:
    if m := re.match(SPLIT_NAME_TYPE_DESC_PATTERN, lines[0]):
        name, type_, desc = m.groups()
    elif ":" in lines[0]:
        name, desc = lines[0].split(":", maxsplit=1)
        type_ = ""
    else:
        name, type_, desc = lines[0], "", ""
    return name, type_, "\n".join([desc.strip(), *lines[1:]])


def _split_item_numpy(lines: list[str]) -> tuple[str, str, str]:
    if ":" in lines[0]:
        name, type_ = lines[0].split(":", maxsplit=1)
    else:
        name, type_ = lines[0], ""
    return name.strip(), type_.strip(), "\n".join(lines[1:])


def split_item(item: str, style: Style) -> tuple[str, str, str]:
    """Return a tuple of (name, type, description)."""
    lines = [line.strip() for line in item.split("\n")]
    if style == "google":
        return _split_item_google(lines)
    return _split_item_numpy(lines)


def iter_items(
    section: str,
    style: Style,
    section_name: str = "Parameters",
) -> Iterator[Item]:
    """Yiled a tuple of (name, type, description) of item.

    If name is 'Raises', the type of [Item] is set by its name.
    """
    for item in _iter_items(section):
        name, type_, desc = split_item(item, style)
        if section_name != "Raises":
            yield Item(name, type_, desc)
        else:
            yield Item(name, name, desc)


@dataclass
class Section(Item):  # noqa: D101
    items: list[Item]

    def __iter__(self) -> Iterator[Item]:
        return iter(self.items)

    def get(self, name: str) -> Item | None:  # noqa: D102
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
    if style == "google" or len(lines := doc.split("\n")) < 3:  # noqa: PLR2004
        return [doc]
    if not lines[2].startswith(" "):  # 2 == after '----' line.
        return [doc]
    return doc.split("\n\n")


SECTION_NAMES: list[tuple[str, ...]] = [
    ("Parameters", "Arguments", "Args"),
    ("Attributes",),
    ("Examples", "Example"),
    ("Returns", "Return"),
    ("Raises", "Raise"),
    ("Yields", "Yield"),
    ("Warnings", "Warns"),
    ("Warnings", "Warns"),
    ("Note",),
    ("Notes",),
]


def _rename_section(section_name: str) -> str:
    for section_names in SECTION_NAMES:
        if section_name in section_names:
            return section_names[0]
    return section_name


def _iter_sections(doc: str, style: Style) -> Iterator[tuple[str, str]]:
    """Yield (section name, description) pairs by splitting the whole docstring."""
    prev_name, prev_desc = "", ""
    for section in _split_sections(doc, style):
        if not section:
            continue
        name, desc = split_section(section, style)
        if not desc:
            continue
        name = _rename_section(name)
        if prev_name == name == "":  # continuous 'plain' section.
            prev_desc = f"{prev_desc}\n\n{desc}" if prev_desc else desc
            continue
        elif prev_name == "" and name != "" and prev_desc:
            yield prev_name, prev_desc
        yield name, desc
        prev_name, prev_desc = name, ""
    if prev_desc:
        yield "", prev_desc


def split_section(section: str, style: Style) -> tuple[str, str]:
    """Return section name and its description."""
    lines = section.split("\n")
    if len(lines) < 2:  # noqa: PLR2004
        return "", section
    if style == "google" and re.match(r"^([A-Za-z0-9][^:]*):$", lines[0]):
        return lines[0][:-1], join_without_first_indent(lines[1:])
    if style == "numpy" and re.match(r"^-+?$", lines[1]):
        return lines[0], join_without_first_indent(lines[2:])
    return "", section


def iter_sections(doc: str, style: Style) -> Iterator[Section]:
    """Yield [Section] instance by splitting the whole docstring."""
    for name, desc in _iter_sections(doc, style):
        type_ = desc_ = ""
        items: list[Item] = []
        if name in ["Parameters", "Attributes", "Raises"]:
            items = list(iter_items(desc, style, name))
        elif name in ["Returns", "Yields"]:
            type_, desc_ = split_return(desc, style)
        elif name in ["Note", "Notes", "Warning", "Warnings"]:
            desc_ = add_admonition(name, desc)
        else:
            desc_ = desc
        yield Section(name, type_, desc_, items)


def split_return(section: str, style: Style) -> tuple[str, str]:
    """Return a tuple of (type, description) for Returns and Yields section."""
    lines = section.split("\n")
    if style == "google" and ":" in lines[0]:
        type_, desc = lines[0].split(":", maxsplit=1)
        return type_.strip(), "\n".join([desc.strip(), *lines[1:]])
    if style == "numpy" and len(lines) > 1 and lines[1].startswith(" "):
        return lines[0], join_without_first_indent(lines[1:])
    return "", section


# for mkapi.objects.Attribute.docstring / property
def split_attribute(docstring: str) -> tuple[str, str]:
    """Return a tuple of (type, description) for the Attribute docstring."""
    return split_return(docstring, "google")


@dataclass(repr=False)
class Docstring(Item):  # noqa: D101
    sections: list[Section]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(num_sections={len(self.sections)})"

    def __iter__(self) -> Iterator[Section]:
        return iter(self.sections)

    def get(self, name: str) -> Section | None:  # noqa: D102
        return get_by_name(self.sections, name)


def parse(doc: str, style: Style) -> Docstring:
    """Return a [Docstring] instance."""
    doc = add_fence(doc)
    sections = list(iter_sections(doc, style))
    return Docstring("", "", "", sections)


def merge_items(a: list[Item], b: list[Item]) -> list[Item]:
    """Merge two lists of [Item] and return a newly created [Docstring] list."""
    items: list[Item] = []
    for name in unique_names(a, b):
        ai, bi = get_by_name(a, name), get_by_name(b, name)
        if not ai:
            items.append(bi)  # type: ignore
        elif not bi:
            items.append(ai)  # type: ignore
        else:
            name_ = ai.name if ai.name else bi.name
            type_ = ai.type if ai.type else bi.type
            desc = ai.description if ai.description else bi.description
            items.append(Item(name_, type_, desc))
    return items


def merge_sections(a: Section, b: Section) -> Section:
    """Merge two [Section] instances into one [Section] instance."""
    if a.name != b.name:
        raise ValueError
    type_ = a.type if a.type else b.type
    desc = f"{a.description}\n\n{b.description}".strip()
    items = merge_items(a.items, b.items)
    return Section(a.name, type_, desc, items)


def merge(a: Docstring, b: Docstring) -> Docstring:  # noqa: PLR0912, C901
    """Merge two [Docstring] instances into one [Docstring] instance."""
    if not a.sections:
        return b
    if not b.sections:
        return a
    names = [name for name in unique_names(a.sections, b.sections) if name]
    sections: list[Section] = []
    for ai in a.sections:
        if ai.name:
            break
        sections.append(ai)
    for name in names:
        ai, bi = get_by_name(a.sections, name), get_by_name(b.sections, name)
        if not ai:
            sections.append(bi)  # type: ignore
        elif not bi:
            sections.append(ai)  # type: ignore
        else:
            sections.append(merge_sections(ai, bi))
    is_named_section = False
    for section in a.sections:
        if section.name:
            is_named_section = True
        elif is_named_section:
            sections.append(section)
    for section in b.sections:
        if not section.name:
            sections.append(section)  # noqa: PERF401
    name_ = a.name if a.name else b.name
    type_ = a.type if a.type else b.type
    desc = a.description if a.description else b.description
    return Docstring(name_, type_, desc, sections)
