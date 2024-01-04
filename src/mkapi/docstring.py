"""Parse docstring."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from mkapi.utils import add_admonition, add_fence, join_without_first_indent

if TYPE_CHECKING:
    from collections.abc import Iterator

type Style = Literal["google", "numpy"]


@dataclass
class Item:  # noqa: D101
    name: str
    type: str  # noqa: A003
    description: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


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


def iter_items(section: str, style: Style) -> Iterator[Item]:
    """Yiled a tuple of (name, type, description) of item."""
    for item in _iter_items(section):
        yield Item(*split_item(item, style))


SPLIT_SECTION_PATTERNS: dict[Style, re.Pattern[str]] = {
    "google": re.compile(r"\n\n\S"),
    "numpy": re.compile(r"\n\n\n|\n\n.+?\n-+\n"),
}


def _iter_sections(doc: str, style: Style) -> Iterator[str]:
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


def iter_sections(doc: str, style: Style) -> Iterator[tuple[str, str]]:
    """Yield (section name, description) pairs by splitting the whole docstring."""
    prev_name, prev_desc = "", ""
    for section in _iter_sections(doc, style):
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


def split_return(section: str, style: Style) -> tuple[str, str]:
    """Return a tuple of (type, description) for Returns and Yields section."""
    lines = section.split("\n")
    if style == "google" and ":" in lines[0]:
        type_, desc = lines[0].split(":", maxsplit=1)
        return type_.strip(), "\n".join([desc.strip(), *lines[1:]])
    if style == "numpy" and len(lines) > 1 and lines[1].startswith(" "):
        return lines[0], join_without_first_indent(lines[1:])
    return "", section


# for mkapi.ast.Attribute.docstring
def split_attribute(docstring: str) -> tuple[str, str]:
    """Return a tuple of (type, description) for Attribute docstring."""
    return split_return(docstring, "google")


@dataclass
class Section(Item):  # noqa: D101
    items: list[Item]

    def __iter__(self) -> Iterator[Item]:
        return iter(self.items)

    def get(self, name: str) -> Item | None:  # noqa: D102
        for item in self.items:
            if item.name == name:
                return item
        return None


@dataclass(repr=False)
class Docstring(Item):  # noqa: D101
    sections: list[Section]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(num_sections={len(self.sections)})"

    def __iter__(self) -> Iterator[Section]:
        return iter(self.sections)

    def get(self, name: str) -> Section | None:  # noqa: D102
        for section in self.sections:
            if section.name == name:
                return section
        return None


def parse_docstring(doc: str, style: Style) -> Docstring:
    """Return a docstring instance."""
    doc = add_fence(doc)
    sections: list[Section] = []
    for name, desc in iter_sections(doc, style):
        type_ = desc_ = ""
        items: list[Item] = []
        if name in ["Parameters", "Attributes", "Raises"]:
            items = list(iter_items(desc, style))
        elif name in ["Returns", "Yields"]:
            type_, desc_ = split_return(desc, style)
        elif name in ["Note", "Notes", "Warning", "Warnings"]:
            desc_ = add_admonition(name, desc)
        else:
            desc_ = desc
        sections.append(Section(name, type_, desc_, items))
    return Docstring("", "", "", sections)


# @dataclass
# class Base:
#     """Base class."""

#     name: str
#     """Name of item."""
#     docstring: str | None
#     """Docstring of item."""

#     def __repr__(self) -> str:
#         return f"{self.__class__.__name__}({self.name!r})"


# @dataclass
# class Nodes[T]:
#     """Collection of [Node] instance."""

#     items: list[T]

#     def __getitem__(self, index: int | str) -> T:
#         if isinstance(index, int):
#             return self.items[index]
#         names = [item.name for item in self.items]  # type: ignore  # noqa: PGH003
#         return self.items[names.index(index)]

#     def __getattr__(self, name: str) -> T:
#         return self[name]

#     def __iter__(self) -> Iterator[T]:
#         return iter(self.items)

#     def __contains__(self, name: str) -> bool:
#         return any(name == item.name for item in self.items)  # type: ignore  # noqa: PGH003

#     def __repr__(self) -> str:
#         names = ", ".join(f"{item.name!r}" for item in self.items)  # type: ignore  # noqa: PGH003
#         return f"{self.__class__.__name__}({names})"


# @dataclass(repr=False)
# class Import(Node):
#     """Import class."""

#     _node: ast.Import | ImportFrom
#     fullanme: str


# @dataclass
# class Imports(Nodes[Import]):
#     """Imports class."""


#             self.markdown = add_fence(self.markdown)
# def postprocess_sections(sections: list[Section]) -> None:
#     for section in sections:
#         if section.name in ["Note", "Notes", "Warning", "Warnings"]:
#             markdown = add_admonition(section.name, section.markdown)
#             if sections and sections[-1].name == "":
#                 sections[-1].markdown += "\n\n" + markdown
#                 continue
#             section.name = ""
#             section.markdown = markdown
