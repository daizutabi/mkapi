"""This module provides functions that parse docstring."""

import inspect
import re
from typing import Any, Iterator, List, Tuple

from mkapi.core.base import Docstring, Item, Section, Type
from mkapi.core.preprocess import replace_link
from mkapi.core.signature import Signature

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


def get_indent(line: str) -> int:
    indent = 0
    for x in line:
        if x != " ":
            return indent
        indent += 1
    return -1


def join(lines):
    indent = get_indent(lines[0])
    return "\n".join(line[indent:] for line in lines).strip()


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
    """Yields list of parameter string.

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


def parse_parameter(lines: List[str], style: str) -> Tuple[str, str, str]:
    """Yields (name, markdown, type).

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
    return name, "\n".join(parsed), type


def parse_parameters(doc: str, style: str) -> List[Tuple[str, str, str]]:
    """Returns list of (name, markdown, type)."""
    return [parse_parameter(lines, style) for lines in split_parameter(doc)]


def parse_returns(doc: str, style: str) -> Tuple[str, str]:
    """Returns (markdown, type)."""
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
    return join(lines), type


def create_section(name: str, doc: str, style: str) -> Section:
    """Returns a `Section` instance."""
    type = ""
    markdown = ""
    items = []
    if name in ["Parameters", "Attributes", "Raises"]:
        items = [Item(n, m, Type(t)) for n, m, t in parse_parameters(doc, style)]
    elif name in ["Returns", "Yields"]:
        markdown, type = parse_returns(doc, style)
    else:
        markdown = doc
    return Section(name, markdown, items, Type(type))


def parse_property(doc: Docstring, obj: Any):
    """Parses property's docstring to inspect type."""
    section = doc.sections[0]
    markdown = section.markdown
    line = markdown.split("\n")[0]
    if ":" in line:
        index = line.index(":")
        doc.type = Type(line[:index].strip())
        section.markdown = markdown[index + 1 :].strip()
    if not doc.type and hasattr(obj, "fget"):
        doc.type = Type(Signature(obj.fget).returns)


def postprocess(doc: Docstring, obj: Any):
    if isinstance(obj, property):
        parse_property(doc, obj)
    if not callable(obj):
        return
    signature = Signature(obj)
    if signature.signature is None:
        return

    def get_type(type: str) -> Type:
        if type.startswith("("):  # tuple
            type = type[1:-1]
        return Type(type)

    if doc["Parameters"] is not None:
        for item in doc["Parameters"].items:
            if not item.type and item.name in signature.parameters:
                item.type = get_type(signature.parameters[item.name])
            if "{default}" in item.markdown and item.name in signature:
                default = signature.defaults[item.name]
                item.markdown = item.markdown.replace("{default}", default)

    if doc["Attributes"] is not None and signature.attributes:
        for item in doc["Attributes"].items:
            if not item.type and item.name in signature.attributes:
                item.type = get_type(signature.attributes[item.name])

    for name in ["Returns", "Yields"]:
        section = doc[name]
        if section is not None and not section.type:
            section.type = Type(getattr(signature, name.lower()))

    if doc["Returns"] is None and doc["Yields"] is None:
        from mkapi.core.node import get_kind

        kind = get_kind(obj)
        if kind == "generator":
            doc.type = Type(signature.yields)
        else:
            doc.type = Type(signature.returns)

    for section in doc.sections:
        if section.name in ["Example", "Examples"]:
            break
        if section.markdown:
            section.markdown = replace_link(obj, section.markdown)
        else:
            for item in section.items:
                if item.markdown:
                    item.markdown = replace_link(obj, item.markdown)


def get_docstring(obj: Any) -> Docstring:
    """Returns a `Docstring` instance."""
    doc = inspect.getdoc(obj)
    if not doc:
        return Docstring()
    sections = []
    for section in split_section(doc):
        sections.append(create_section(*section))
    docstring = Docstring(sections)
    postprocess(docstring, obj)
    return docstring
