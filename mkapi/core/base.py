"""This module provides entity classes to represent docstring structure."""
from dataclasses import dataclass, field
from typing import Iterator, List, Optional


@dataclass
class Base:
    """Base class.

    Args:
        name: Object name.
        type: Object type.
        markdown: Markdown source.

    Attributes:
        name: Object name.
        type: Object type.
        type_html: Object type html after adding links.
        markdown: Markdown source.
        html: HTML after conversion.
    """

    name: str = ""
    type: str = ""
    markdown: str = ""
    html: str = field(default="", init=False)
    type_html: str = field(default="", init=False)

    def set_html(self, html: str):
        """Sets `html` attribute."""
        self.html = html


@dataclass
class Item(Base):
    """Item class represents an item in Parameters, Attributes, and Raises sections."""

    def set_html(self, html: str):
        """Sets `html` attribute cleaning `p` tags."""
        html = html.replace("<p>", "").replace("</p>", "<br>")
        if html.endswith("<br>"):
            html = html[:-4]
        self.html = html


@dataclass
class Section(Base):
    """Section class represents a section in docstring.

    Args:
        items: List for Arguments, Attributes, or Exceptions sections.

    Attributes:
        items: List for Arguments, Attributes, or Exceptions sections.

    Examples:
        `Section` is iterable:
        >>> section = Section('Returns', markdown='Returns an integer.')
        >>> for x in section:
        ...     assert x is section

        >>> items = [Item('x'), Item('y'), Item('z')]
        >>> section = Section('Parameters', items=items)
        >>> [item.name for item in section]
        ['x', 'y', 'z']

        Indexing:
        >>> isinstance(section['y'], Item)
        True
        >>> section['z'].name
        'z'

        Contains:
        >>> 'x' in section
        True
    """

    items: List[Item] = field(default_factory=list)

    def __iter__(self) -> Iterator[Base]:
        if self.markdown:
            yield self
        else:
            yield from self.items

    def __getitem__(self, name) -> Optional[Item]:
        for item in self.items:
            if item.name == name:
                return item
        return None

    def __contains__(self, name) -> bool:
        return self[name] is not None


@dataclass
class Docstring:
    """Docstring class represents a docstring of an object.

    Args:
        sections: List of Section instance.
        type: Type for Returns and Yields sections.

    Attributes:
        sections: List of Section instance.
        type: Type for Returns and Yields sections.

    Examples:
        Empty docstring:
        >>> docstring = Docstring()
        >>> assert not docstring

        Docstring with 3 sections:
        >>> default = Section("", markdown="Default")
        >>> parameters = Section("Parameters", items=[Item("a"), Item("b")])
        >>> returns = Section("Returns", markdown="Returned Value")
        >>> docstring = Docstring([default, parameters, returns])

        `Docstring` is iterable:
        >>> [base.name for base in docstring]
        ['', 'a', 'b', 'Returns']

        Indexing:
        >>> docstring["Parameters"].items[0].name
        'a'
    """

    sections: List[Section] = field(default_factory=list)
    type: str = ""

    def __bool__(self):
        return len(self.sections) > 0

    def __iter__(self) -> Iterator[Base]:
        for section in self.sections:
            yield from section

    def __getitem__(self, name: str) -> Optional[Section]:
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def __setitem__(self, name: str, section: Section):
        for k, section_ in enumerate(self.sections):
            if section_.name == name:
                self.sections[k] = section
                return
            if name == "Parameters" and section_.name != "":
                self.sections.insert(k, section)
                return
            if section_.name in ["Raises", "Yields", "Returns"]:
                self.sections.insert(k, section)
                return
        self.sections.append(section)
