"""Parse docstrings."""
from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import mkapi.markdown
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


@dataclass
class Item:
    name: str
    type: str
    text: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


TYPE_STRING_PATTERN = re.compile(r"\[__mkapi__.(\S+?)\]\[\]")


def iter_items(text: str, style: Style) -> Iterator[Item]:
    """Yield [Item] instances."""
    for item in _iter_items(text):
        name, type_, text = split_item(item, style)

        type_ = TYPE_STRING_PATTERN.sub(r"\1", type_)
        yield Item(name, type_, text)


def iter_items_without_name(text: str, style: Style) -> Iterator[Item]:
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


@dataclass(repr=False)
class Section(Item):
    """Section class of docstring."""

    items: list[Item]


def _create_admonition(name: str, text: str) -> Section:
    if name.startswith("Note"):
        kind = "note"

    elif name.startswith("Warning"):
        kind = "warning"

    elif name.startswith("See Also"):
        kind = "info"
        text = mkapi.markdown.get_see_also(text)

    else:
        raise NotImplementedError

    text = mkapi.markdown.get_admonition(kind, name, text)
    return Section("", "", text, [])


def iter_sections(text: str, style: Style) -> Iterator[Section]:
    """Yield [Section] instances by splitting a docstring."""
    for name, text_ in _iter_sections(text, style):
        if name in ["Parameters", "Attributes", "Raises"]:
            items = list(iter_items(text_, style))
            yield Section(name, "", "", items)

        elif name in ["Returns", "Yields"]:
            items = list(iter_items_without_name(text_, style))
            yield Section(name, "", "", items)

        elif name in ["Note", "Notes", "Warning", "Warnings", "See Also"]:
            yield _create_admonition(name, text_)

        else:
            yield Section(name, "", text_, [])


@dataclass
class Doc(Item):
    """Doc class."""

    sections: list[Section]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(sections={len(self.sections)})"


def create_doc(text: str | None, style: Style | None = None) -> Doc:
    """Return a [Doc] instance."""
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
    type_, text = split_item_without_name(text, "google")
    return Doc("Doc", type_, text, [])


def split_type(doc: Doc) -> None:
    if not doc.type and doc.text:
        doc.type, doc.text = split_item_without_name(doc.text, "google")


def create_summary_item(name: str, doc: Doc, type_: str = ""):
    text = doc.text.split("\n\n")[0]  # summary line
    return Item(name, type_, text)


def merge_items(a: Item, b: Item) -> Item:
    type_ = a.type or b.type
    text = f"{a.text}\n\n{b.text}".strip()
    return Item(a.name, type_, text)


def iter_merged_items(a: list[Item], b: list[Item]) -> Iterator[Item]:
    """Yield merged [Item] instances."""
    for name in unique_names(a, b):
        ai, bi = get_by_name(a, name), get_by_name(b, name)

        if ai and not bi:
            yield ai

        elif not ai and bi:
            yield bi

        elif ai and bi:
            yield merge_items(ai, bi)


def merge_sections(a: Section, b: Section) -> Section:
    """Merge two [Section] instances into one [Section] instance."""
    type_ = a.type or b.type
    text = f"{a.text}\n\n{b.text}".strip()
    items = iter_merged_items(a.items, b.items)
    return Section(a.name, type_, text, list(items))


def iter_merged_sections(a: list[Section], b: list[Section]) -> Iterator[Section]:
    """Yield merged [Section] instances from two lists of [Section]."""
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
    """Merge two [Docstring] instances into one [Docstring] instance."""
    type_ = a.type or b.type
    text = f"{a.text}\n\n{b.text}".strip()
    sections = iter_merged_sections(a.sections, b.sections)
    return Doc("Doc", type_, text, list(sections))


def is_empty(doc: Doc) -> bool:
    """Return True if a [Doc] instance is empty."""
    if doc.text:
        return False

    for section in doc.sections:
        if section.text:
            return False

        for item in section.items:
            if item.text:
                return False

    return True
