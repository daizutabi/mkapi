import inspect
import re
from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional, Tuple

from mkapi.core.signature import Signature

SECTIONS = [
    "Args",
    "Arguments",
    "Attributes",
    "Example",
    "Examples",
    "Note",
    "Notes",
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
    return "\n".join(line[indent:] for line in lines)


def rename_section(name: str) -> str:
    if name in ["Args", "Arguments"]:
        return "Parameters"
    if name == "Warns":
        return "Warnings"
    return name


def split_section(doc: str) -> Iterator[Tuple[str, str]]:
    """Yields section name and its contents."""
    lines = [x.rstrip() for x in doc.split("\n")]
    name = ""
    start = indent = 0
    for stop, line in enumerate(lines, 1):
        if stop == len(lines):
            next_indent = -1
        else:
            next_indent = get_indent(lines[stop])
        if not line and next_indent < indent:
            if start < stop - 1:
                yield name, join(lines[start : stop - 1])
            start = stop
            name = ""
        elif line.endswith(":") and line[:-1] in SECTIONS:
            if start < stop - 1:
                yield name, join(lines[start : stop - 1])
            name = rename_section(line[:-1])
            start = stop
            indent = next_indent
    if start < len(lines):
        yield name, join(lines[start:])


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


def parse_parameter(lines: List[str]) -> Tuple[str, str, str]:
    """Yields (name, type, markdown)."""
    name, _, line = lines[0].partition(":")
    name = name.strip()
    line = line.strip()
    parsed = [line]
    if len(lines) > 1:
        indent = get_indent(lines[1])
        for line in lines[1:]:
            parsed.append(line[indent:])
    m = re.match(r"(.*?)\s*?\((.*?)\)", name)
    if m:
        name, type = m.group(1), m.group(2)
    else:
        type = ""
    return name, type, "\n".join(parsed)


def parse_parameters(doc: str) -> List[Tuple[str, str, str]]:
    """Returns list of (name, type, markdown)."""
    return [parse_parameter(lines) for lines in split_parameter(doc)]


def parse_returns(doc: str) -> Tuple[str, str]:
    """Returns (type, markdown)."""
    lines = doc.split("\n")
    if ":" in lines[0]:
        type, _, lines[0] = lines[0].partition(":")
        type = type.strip()
        lines[0] = lines[0].strip()
    else:
        type = ""
    return type, "\n".join(lines)


def parse_raise(lines: List[str]) -> Tuple[str, str]:
    """Returns (type, markdown)."""
    type, _, markdown = parse_parameter(lines)
    return type, markdown


def parse_raises(doc: str) -> List[Tuple[str, str]]:
    return [parse_raise(lines) for lines in split_parameter(doc)]


@dataclass
class Item:
    name: str
    type: str
    markdown: str
    html: str = ""

    def set_html(self, html):
        html = html.replace("<p>", "").replace("</p>", "<br>")
        if html.endswith("<br>"):
            html = html[:-4]
        self.html = html


@dataclass
class Section:
    name: str
    type: str = ""
    markdown: str = ""
    items: List[Item] = field(default_factory=list)
    html: str = ""

    def __getitem__(self, index):
        return self.items[index]

    def __len__(self):
        return len(self.items)

    def __getattr__(self, name):
        for item in self.items:
            if item.name == name:
                return item

    def __iter__(self):
        if self.markdown:
            yield self
        else:
            yield from self.items

    def set_html(self, html):
        self.html = html


@dataclass
class Docstring:
    obj: Optional[Any] = field(repr=False)
    sections: List[Section]

    def __getattr__(self, name):
        for section in self.sections:
            if section.name == name:
                return section

    def __getitem__(self, name):
        return getattr(self, name)

    def __len__(self):
        return len(self.sections)

    def __iter__(self):
        for section in self.sections:
            yield from section


def create_section(name: str, doc: str) -> Section:
    type = ""
    markdown = ""
    items = []
    if name in ["Parameters", "Attributes"]:
        items = [Item(n, t, m) for n, t, m in parse_parameters(doc)]
    elif name == "Raises":
        items = [Item(t, "", m) for t, m in parse_raises(doc)]
    elif name in ["Returns", "Yields"]:
        type, markdown = parse_returns(doc)
    else:
        markdown = doc
    return Section(name, type=type, markdown=markdown, items=items)


def postprocess(doc: Docstring, obj: Any):
    if isinstance(obj, property):
        section = doc.sections[0]
        markdown = section.markdown
        line = markdown.split("\n")[0]
        if ":" in line:
            index = line.index(":")
            section.type = line[:index].strip()
            section.markdown = markdown[index + 1 :].strip()

    if not callable(obj):
        return

    annotations = Signature(obj).annotations
    if doc["Parameters"]:
        for item in doc["Parameters"]:
            if item.type == "" and item.name in annotations[0]:
                item.type = annotations[0][item.name]

    for k, name in enumerate(["Returns", "Yields"], 1):
        if doc[name] is not None:
            section = doc[name]
            if section.type == "":
                section.type = annotations[k]  # type:ignore


def parse_docstring(obj: Any) -> Docstring:
    doc = inspect.getdoc(obj)
    if not doc:
        return Docstring(obj, [])
    sections = []
    for section in split_section(doc):
        sections.append(create_section(*section))
    docstring = Docstring(obj, sections)
    postprocess(docstring, obj)
    return docstring
