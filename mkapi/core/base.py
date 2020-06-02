from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional

import mkapi.core.preprocess
from mkapi.core.inspect import Signature


@dataclass
class Base:
    name: str
    type: str = ""
    markdown: str = ""
    html: str = ""

    def set_html(self, html):
        """Sets `html` attribute according to the givin `html` argument.

        In the simplest case, just store the argument to the attribute. But modify
        the attribute if necessary.
        """
        self.html = html


@dataclass
class Item(Base):
    def set_html(self, html):
        html = html.replace("<p>", "").replace("</p>", "<br>")
        if html.endswith("<br>"):
            html = html[:-4]
        self.html = html


@dataclass
class Section(Base):
    items: List[Item] = field(default_factory=list)

    def __iter__(self) -> Iterator[Base]:
        if self.markdown:
            yield self
        else:
            yield from self.items


@dataclass
class Docstring:
    sections: List[Section]
    type: str = ""

    def __getitem__(self, name) -> Optional[Section]:
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def __iter__(self) -> Iterator[Base]:
        for section in self.sections:
            yield from section


@dataclass
class Node(Base):
    obj: Any = field(default=None, repr=False)
    depth: int = 0
    prefix: str = ""
    kind: str = ""
    sourcefile: str = ""
    lineno: int = 0
    signature: Optional[Signature] = None
    docstring: Optional[Docstring] = None
    members: List["Node"] = field(default_factory=list)

    def __post_init__(self):
        if self.prefix:
            self.id = ".".join([self.prefix, self.name])
        else:
            self.id = self.name

    def __getitem__(self, index):
        return self.members[index]

    def __len__(self):
        return len(self.members)

    def __getattr__(self, name):
        for member in self.members:
            if member.name == name:
                return member

    def __iter__(self) -> Iterator[Base]:
        if self.docstring:
            yield from self.docstring
        for member in self.members:
            yield from member

    def get_markdown(self) -> str:
        markdowns = []
        for base in self:
            markdown = mkapi.core.preprocess.convert(base.markdown)
            markdowns.append(markdown)
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def set_html(self, html: str):
        for base, html in zip(self, html.split("<!-- mkapi:sep -->")):
            base.set_html(html.strip())
