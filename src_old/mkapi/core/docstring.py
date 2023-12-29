"""Parse docstring."""
import inspect
import re
from collections.abc import Iterator
from dataclasses import is_dataclass

from mkapi.core.base import Docstring, Inline, Item, Section, Type
from mkapi.core.link import get_link, replace_link
from mkapi.core.object import get_mro
from mkapi.core.preprocess import add_admonition, get_indent, join_without_indent
from mkapi.inspect.signature import Signature, get_signature

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


def rename_section(name: str) -> str:  # noqa: D103
    if name in ["Args", "Arguments"]:
        return "Parameters"
    if name == "Warns":
        return "Warnings"
    return name


def section_heading(line: str) -> tuple[str, str]:
    """Return a tuple of (section name, style name).

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
    if line.endswith(":") and line[:-1] in SECTIONS:
        return line[:-1], "google"
    return "", ""


def split_section(doc: str) -> Iterator[tuple[str, str, str]]:
    r"""Yield a tuple of (section name, contents, style).

    Args:
        doc: Docstring

    Examples:
        >>> doc = "abc\n\nArgs:\n    x: X\n"
        >>> it = split_section(doc)
        >>> next(it)
        ('', 'abc', '')
        >>> next(it)
        ('Parameters', 'x: X', 'google')
    """
    name = style = ""
    start = indent = 0
    lines = [x.rstrip() for x in doc.split("\n")]
    for stop, line in enumerate(lines, 1):
        next_indent = -1 if stop == len(lines) else get_indent(lines[stop])
        if not line and next_indent < indent and name:
            if start < stop - 1:
                yield name, join_without_indent(lines[start : stop - 1]), style
            start, name = stop, ""
        else:
            section, style_ = section_heading(line)
            if section:
                if start < stop - 1:
                    yield name, join_without_indent(lines[start : stop - 1]), style
                style, start, name = style_, stop, rename_section(section)
                if style == "numpy":  # skip underline without counting the length.
                    start += 1
                indent = next_indent
    if start < len(lines):
        yield name, join_without_indent(lines[start:]), style


def split_parameter(doc: str) -> Iterator[list[str]]:
    """Yield a list of parameter string.

    Args:
        doc: Docstring
    """
    start = stop = 0
    lines = [x.rstrip() for x in doc.split("\n")]
    for stop, _ in enumerate(lines, 1):
        next_indent = 0 if stop == len(lines) else get_indent(lines[stop])
        if next_indent == 0:
            yield lines[start:stop]
            start = stop


PARAMETER_PATTERN = {
    "google": re.compile(r"(.*?)\s*?\((.*?)\)"),
    "numpy": re.compile(r"([^ ]*?)\s*:\s*(.*)"),
}


def parse_parameter(lines: list[str], style: str) -> Item:
    """Return a Item instance corresponding to a parameter.

    Args:
        lines: Splitted parameter docstring lines.
        style: Docstring style. `google` or `numpy`.
    """
    if style == "google":
        name, _, line = lines[0].partition(":")
        name, parsed = name.strip(), [line.strip()]
    else:
        name, parsed = lines[0].strip(), []
    if len(lines) > 1:
        indent = get_indent(lines[1])
        for line in lines[1:]:
            parsed.append(line[indent:])
    if m := re.match(PARAMETER_PATTERN[style], name):
        name, type_ = m.group(1), m.group(2)
    else:
        type_ = ""
    return Item(name, Type(type_), Inline("\n".join(parsed)))


def parse_parameters(doc: str, style: str) -> list[Item]:
    """Return a list of Item."""
    return [parse_parameter(lines, style) for lines in split_parameter(doc)]


def parse_returns(doc: str, style: str) -> tuple[str, str]:
    """Return a tuple of (type, markdown)."""
    type_, lines = "", doc.split("\n")
    if style == "google":
        if ":" in lines[0]:
            type_, _, lines[0] = lines[0].partition(":")
            type_ = type_.strip()
            lines[0] = lines[0].strip()
    else:
        type_, lines = lines[0].strip(), lines[1:]
    return type_, join_without_indent(lines)


def get_section(name: str, doc: str, style: str) -> Section:
    """Return a [Section]() instance."""
    type_ = markdown = ""
    items = []
    if name in ["Parameters", "Attributes", "Raises"]:
        items = parse_parameters(doc, style)
    elif name in ["Returns", "Yields"]:
        type_, markdown = parse_returns(doc, style)
    else:
        markdown = doc
    return Section(name, markdown, items, Type(type_))


def parse_bases(doc: Docstring, obj: object) -> None:
    """Parse base classes to create a Base(s) line."""
    if not inspect.isclass(obj) or not hasattr(obj, "mro"):
        return
    objs = get_mro(obj)[1:]
    if not objs:
        return
    types = [get_link(obj_, include_module=True) for obj_ in objs]
    items = [Item(type=Type(type_)) for type_ in types if type_]
    doc.set_section(Section("Bases", items=items))


def parse_source(doc: Docstring, obj: object) -> None:
    """Parse parameters' docstring to inspect type and description from source.

    Examples:
        >>> from mkapi.core.base import Base
        >>> doc = Docstring()
        >>> parse_source(doc, Base)
        >>> section = doc["Parameters"]
        >>> section["name"].to_tuple()
        ('name', 'str, optional', 'Name of self.')
        >>> section = doc["Attributes"]
        >>> section["html"].to_tuple()
        ('html', 'str', 'HTML output after conversion.')
    """
    signature = get_signature(obj)
    name = "Parameters"
    section: Section = signature[name]
    if name in doc:
        section = section.merge(doc[name], force=True)
    if section:
        doc.set_section(section, replace=True)

    name = "Attributes"
    section: Section = signature[name]
    if name not in doc and not section:
        return
    doc[name].update(section)
    if is_dataclass(obj) and "Parameters" in doc:
        for item in doc["Parameters"].items:
            if item.name in section:
                doc[name].set_item(item)


def postprocess_parameters(doc: Docstring, signature: Signature) -> None:  # noqa: D103
    if "Parameters" not in doc:
        return
    for item in doc["Parameters"].items:
        description = item.description
        if "{default}" in description.name and item.name in signature:
            default = signature.defaults[item.name]
            description.markdown = description.name.replace("{default}", default)


def postprocess_returns(doc: Docstring, signature: Signature) -> None:  # noqa: D103
    for name in ["Returns", "Yields"]:
        if name in doc:
            section = doc[name]
            if not section.type:
                section.type = Type(getattr(signature, name.lower()))


def postprocess_sections(doc: Docstring, obj: object) -> None:  # noqa: D103
    sections: list[Section] = []
    for section in doc.sections:
        if section.name not in ["Example", "Examples"]:
            for base in section:
                base.markdown = replace_link(obj, base.markdown)
        if section.name in ["Note", "Notes", "Warning", "Warnings"]:
            markdown = add_admonition(section.name, section.markdown)
            if sections and sections[-1].name == "":
                sections[-1].markdown += "\n\n" + markdown
                continue
            section.name = ""
            section.markdown = markdown
        sections.append(section)
    doc.sections = sections


def set_docstring_type(doc: Docstring, signature: Signature, obj: object) -> None:  # noqa: D103
    from mkapi.core.node import get_kind

    if "Returns" not in doc and "Yields" not in doc:
        if get_kind(obj) == "generator":
            doc.type = Type(signature.yields)
        else:
            doc.type = Type(signature.returns)


def postprocess_docstring(doc: Docstring, obj: object) -> None:
    """Docstring prostprocess."""
    parse_bases(doc, obj)
    parse_source(doc, obj)

    if not callable(obj):
        return

    signature = get_signature(obj)
    if not signature.signature:
        return

    postprocess_parameters(doc, signature)
    postprocess_returns(doc, signature)
    postprocess_sections(doc, obj)
    set_docstring_type(doc, signature, obj)


def get_docstring(obj: object) -> Docstring:
    """Return a [Docstring]() instance."""
    doc = inspect.getdoc(obj)
    if not doc:
        return Docstring()
    sections = [get_section(*section_args) for section_args in split_section(doc)]
    docstring = Docstring(sections)
    postprocess_docstring(docstring, obj)
    return docstring
