import inspect
import re
from typing import Any, Iterator, List, Optional, Tuple

from mkapi.core.base import Docstring, Item, Section
from mkapi.core.inspect import Annotation

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


def section_header(line: str) -> Tuple[str, str]:
    """Returns a tuple of (section name, style name)."""
    if line in SECTIONS:
        return line, "numpy"
    elif line.endswith(":") and line[:-1] in SECTIONS:
        return line[:-1], "google"
    else:
        return "", ""


def split_section(doc: str) -> Iterator[Tuple[str, str, str]]:
    """Yields a tuple of (section name, contents, style)."""
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
            section, style_ = section_header(line)
            if section:
                style = style_
                if start < stop - 1:
                    yield name, join(lines[start : stop - 1]), style
                name = rename_section(section)
                start = stop
                if style == "numpy":  # skip underline without counting the length.
                    start += 1
                indent = next_indent
    if start < len(lines):
        yield name, join(lines[start:]), style


def split_parameter(doc: str) -> Iterator[List[str]]:
    """Yields list of parameter string."""
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
    """Yields (name, type, markdown)."""
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
    return name, type, "\n".join(parsed)


def parse_parameters(doc: str, style: str) -> List[Tuple[str, str, str]]:
    """Returns list of (name, type, markdown)."""
    return [parse_parameter(lines, style) for lines in split_parameter(doc)]


def parse_raise(lines: List[str], style: str) -> Tuple[str, str]:
    """Returns (type, markdown)."""
    type, _, markdown = parse_parameter(lines, style)
    return type, markdown


def parse_raises(doc: str, style: str) -> List[Tuple[str, str]]:
    return [parse_raise(lines, style) for lines in split_parameter(doc)]


def parse_returns(doc: str, style: str) -> Tuple[str, str]:
    """Returns (type, markdown)."""
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


def create_section(name: str, doc: str, style: str) -> Section:
    type = ""
    markdown = ""
    items = []
    if name in ["Parameters", "Attributes"]:
        items = [Item(n, t, m) for n, t, m in parse_parameters(doc, style)]
    elif name == "Raises":
        items = [Item(t, "", m) for t, m in parse_raises(doc, style)]
    elif name in ["Returns", "Yields"]:
        type, markdown = parse_returns(doc, style)
    else:
        markdown = doc
    return Section(name, type=type, markdown=markdown, items=items)


def parse_property(doc: Docstring, obj: Any):
    section = doc.sections[0]
    markdown = section.markdown
    line = markdown.split("\n")[0]
    if ":" in line:
        index = line.index(":")
        doc.type = line[:index].strip()
        section.markdown = markdown[index + 1 :].strip()
    if not doc.type and hasattr(obj, "fget"):
        doc.type = Annotation(obj.fget).returns


def postprocess(doc: Docstring, obj: Any):
    if isinstance(obj, property):
        parse_property(doc, obj)
    if not callable(obj):
        return

    try:
        annotation = Annotation(obj)
    except ValueError:
        return

    if doc["Parameters"] is not None:
        for item in doc["Parameters"]:
            if item.type == "" and item.name in annotation:
                item.type = annotation[item.name]
                if item.type.startswith("("):  # tuple
                    item.type = item.type[1:-1]
            if "{default}" in item.markdown and item.name in annotation.defaults:
                default = annotation.defaults[item.name]
                item.markdown = item.markdown.replace("{default}", default)

    if doc["Attributes"] is not None and annotation.attributes:
        for item in doc["Attributes"]:
            if item.type == "" and item.name in annotation.attributes:
                item.type = annotation.attributes[item.name]
                if item.type.startswith("("):
                    item.type = item.type[1:-1]

    for name in ["Returns", "Yields"]:
        section = doc[name]
        if section is not None and section.type == "":
            section.type = getattr(annotation, name.lower())

    if doc["Returns"] is None and doc["Yields"] is None:
        doc.type = annotation.returns


def parse_docstring(obj: Any) -> Optional[Docstring]:
    doc = inspect.getdoc(obj)
    if not doc:
        return None
    sections = []
    for section in split_section(doc):
        sections.append(create_section(*section))
    docstring = Docstring(sections)
    postprocess(docstring, obj)
    return docstring
