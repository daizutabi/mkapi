"""This module provides functions that parse docstring."""

import inspect
import re
from dataclasses import is_dataclass
from typing import Any, Iterator, List, Tuple

from mkapi.core import preprocess
from mkapi.core.base import Docstring, Inline, Item, Section, Type
from mkapi.core.linker import get_link, replace_link
from mkapi.core.signature import get_signature
from mkapi.utils import get_indent, join

SECTIONS = [
    "Args",
    "Arguments",
    "Attributes",
    "Example",
    "Examples",
    "Note",
    "Notes",
    "Parameters",
    "Raises",
    "Returns",
    "References",
    "See Also",
    "Todo",
    "Warning",
    "Warnings",
    "Warns",
    "Yield",
    "Yields",
]


def rename_section(name: str) -> str:
    if name in ["Args", "Arguments"]:
        return "Parameters"
    if name == "Warns":
        return "Warnings"
    return name


def section_heading(line: str) -> Tuple[str, str]:
    """Returns a tuple of (section name, style name).

    Args:
        line: Docstring line.

    Examples:
        >>> section_heading("Args:")
        ('Args', 'google')
        >>> section_heading("Raises")
        ('Raises', 'numpy')
        >>> section_heading("other")
        ('', '')
    """
    if line in SECTIONS:
        return line, "numpy"
    elif line.endswith(":") and line[:-1] in SECTIONS:
        return line[:-1], "google"
    else:
        return "", ""


def split_section(doc: str) -> Iterator[Tuple[str, str, str]]:
    """Yields a tuple of (section name, contents, style).

    Args:
        doc: Docstring

    Examples:
        >>> doc = "abc\\n\\nArgs:\\n    x: X\\n"
        >>> it = split_section(doc)
        >>> next(it)
        ('', 'abc', '')
        >>> next(it)
        ('Parameters', 'x: X', 'google')
    """
    lines = [x.rstrip() for x in doc.split("\n")]
    name = ""
    style = ""
    start = indent = 0
    for stop, line in enumerate(lines, 1):
        if stop == len(lines):
            next_indent = -1
        else:
            next_indent = get_indent(lines[stop])
        if not line and next_indent < indent and name:
            if start < stop - 1:
                yield name, join(lines[start : stop - 1]), style
            start = stop
            name = ""
        else:
            section, style_ = section_heading(line)
            if section:
                if start < stop - 1:
                    yield name, join(lines[start : stop - 1]), style
                style = style_
                name = rename_section(section)
                start = stop
                if style == "numpy":  # skip underline without counting the length.
                    start += 1
                indent = next_indent
    if start < len(lines):
        yield name, join(lines[start:]), style


def split_parameter(doc: str) -> Iterator[List[str]]:
    """Yields a list of parameter string.

    Args:
        doc: Docstring
    """
    lines = [x.rstrip() for x in doc.split("\n")]
    start = stop = 0
    for stop, line in enumerate(lines, 1):
        if stop == len(lines):
            next_indent = 0
        else:
            next_indent = get_indent(lines[stop])
        if next_indent == 0:
            yield lines[start:stop]
            start = stop


def parse_parameter(lines: List[str], style: str) -> Item:
    """Returns a Item instance that represents a parameter.

    Args:
        lines: Splitted parameter docstring lines.
        style: Docstring style. `google` or `numpy`.
    """
    if style == "google":
        name, _, line = lines[0].partition(":")
        name = name.strip()
        parsed = [line.strip()]
        pattern = r"(.*?)\s*?\((.*?)\)"
    else:
        name = lines[0].strip()
        parsed = []
        pattern = r"([^ ]*?)\s*:\s*(.*)"
    if len(lines) > 1:
        indent = get_indent(lines[1])
        for line in lines[1:]:
            parsed.append(line[indent:])
    m = re.match(pattern, name)
    if m:
        name, type = m.group(1), m.group(2)
    else:
        type = ""
    return Item(name, Type(type), Inline("\n".join(parsed)))


def parse_parameters(doc: str, style: str) -> List[Item]:
    """Returns a list of Item."""
    return [parse_parameter(lines, style) for lines in split_parameter(doc)]


def parse_returns(doc: str, style: str) -> Tuple[str, str]:
    """Returns a tuple of (type, markdown)."""
    lines = doc.split("\n")
    if style == "google":
        if ":" in lines[0]:
            type, _, lines[0] = lines[0].partition(":")
            type = type.strip()
            lines[0] = lines[0].strip()
        else:
            type = ""
    else:
        type = lines[0].strip()
        lines = lines[1:]
    return type, join(lines)


def get_section(name: str, doc: str, style: str) -> Section:
    """Returns a [Section]() instance."""
    type = ""
    markdown = ""
    items = []
    if name in ["Parameters", "Attributes", "Raises"]:
        items = parse_parameters(doc, style)
    elif name in ["Returns", "Yields"]:
        type, markdown = parse_returns(doc, style)
    else:
        markdown = doc
    return Section(name, markdown, items, Type(type))


def parse_bases(doc: Docstring, obj: Any):
    """Parses base classes to create a Base(s) line."""
    if not inspect.isclass(obj) or not hasattr(obj, "mro"):
        return
    objs = obj.mro()[1:-1]
    if not objs:
        return
    types = [get_link(obj, include_module=True) for obj in objs]
    items = [Item(type=Type(type)) for type in types if type]
    doc.set_section(Section("Bases", items=items))


def parse_source(doc: Docstring, obj: Any):
    """Parses parameters' docstring to inspect type and description from source.

    Examples:
        >>> from mkapi.core.base import Base
        >>> doc = Docstring()
        >>> parse_source(doc, Base)
        >>> section = doc['Parameters']
        >>> section['name'].to_tuple()
        ('name', 'str, optional', 'Name of self.')
        >>> section = doc['Attributes']
        >>> section['html'].to_tuple()
        ('html', 'str', 'HTML output after conversion.')
    """
    signature = get_signature(obj)
    name = "Parameters"
    section = signature[name]
    if name in doc:
        section = section.merge(doc[name], force=True)
    if section:
        doc.set_section(section, replace=True)

    name = "Attributes"
    section = signature[name]
    if name not in doc and not section:
        return
    doc[name].update(section)
    if is_dataclass(obj) and "Parameters" in doc:
        for item in doc["Parameters"].items:
            if item.name in section:
                doc[name].set_item(item)


def postprocess(doc: Docstring, obj: Any):
    parse_bases(doc, obj)
    parse_source(doc, obj)
    if not callable(obj):
        return

    signature = get_signature(obj)
    if signature.signature is None:
        return

    if "Parameters" in doc:
        for item in doc["Parameters"].items:
            description = item.description
            if "{default}" in description.name and item.name in signature:
                default = signature.defaults[item.name]
                description.markdown = description.name.replace("{default}", default)

    for name in ["Returns", "Yields"]:
        if name in doc:
            section = doc[name]
            if not section.type:
                section.type = Type(getattr(signature, name.lower()))

    if "Returns" not in doc and "Yields" not in doc:
        from mkapi.core.node import get_kind

        kind = get_kind(obj)
        if kind == "generator":
            doc.type = Type(signature.yields)
        else:
            doc.type = Type(signature.returns)

    sections: List[Section] = []
    for section in doc.sections:
        if section.name not in ["Example", "Examples"]:
            for base in section:
                base.markdown = replace_link(obj, base.markdown)
        if section.name in ["Note", "Notes", "Warning", "Warnings"]:
            markdown = preprocess.admonition(section.name, section.markdown)
            if sections and sections[-1].name == "":
                sections[-1].markdown += "\n\n" + markdown
                continue
            else:
                section.name = ""
                section.markdown = markdown
        sections.append(section)
    doc.sections = sections


def get_docstring(obj: Any) -> Docstring:
    """Returns a [Docstring]() instance."""
    doc = inspect.getdoc(obj)
    if doc:
        sections = []
        for section in split_section(doc):
            sections.append(get_section(*section))
        docstring = Docstring(sections)
    else:
        return Docstring()
    postprocess(docstring, obj)
    return docstring
