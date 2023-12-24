"""This module provides entity classes to represent docstring structure."""
from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional, Tuple

from mkapi.core import preprocess
from mkapi.core.regex import LINK_PATTERN


@dataclass
class Base:
    """Base class.

    Examples:
        >>> base = Base('x', 'markdown')
        >>> base
        Base('x')
        >>> bool(base)
        True
        >>> list(base)
        [Base('x')]
        >>> base = Base()
        >>> bool(base)
        False
        >>> list(base)
        []
    """

    name: str = ""  #: Name of self.
    markdown: str = ""  #: Markdown source.
    html: str = field(default="", init=False)  #: HTML output after conversion.
    callback: Optional[Callable[["Base"], str]] = field(default=None, init=False)
    """Callback function to modify HTML output."""

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r})"

    def __bool__(self) -> bool:
        """Returns True if name is not empty."""
        return bool(self.name)

    def __iter__(self) -> Iterator["Base"]:
        """Yields self if markdown is not empty."""
        if self.markdown:
            yield self

    def set_html(self, html: str):
        """Sets HTML output.

        Args:
            html: HTML output.
        """
        self.html = html
        if self.callback:
            self.html = self.callback(self)

    def copy(self):
        """Returns a copy of the {class} instance."""
        return self.__class__(name=self.name, markdown=self.markdown)


@dataclass(repr=False)
class Inline(Base):
    """Inline class.

    Examples:
        >>> inline = Inline()
        >>> bool(inline)
        False
        >>> inline = Inline('markdown')
        >>> inline.name == inline.markdown
        True
        >>> inline
        Inline('markdown')
        >>> bool(inline)
        True
        >>> next(iter(inline)) is inline
        True
        >>> inline.set_html("<p>p1</p><p>p2</p>")
        >>> inline.html
        'p1<br>p2'
        >>> inline.copy()
        Inline('markdown')
    """

    markdown: str = field(init=False)

    def __post_init__(self):
        self.markdown = self.name

    def set_html(self, html: str):
        """Sets `html` attribute cleaning `p` tags."""
        html = preprocess.strip_ptags(html)
        super().set_html(html)

    def copy(self):
        return self.__class__(name=self.name)


@dataclass(repr=False)
class Type(Inline):
    """Type class represents type of Item_, Section_, Docstring_, or
    [Object](mkapi.core.structure.Object).

    Examples:
        >>> a = Type('str')
        >>> a
        Type('str')
        >>> list(a)
        []
        >>> b = Type('[Object](base.Object)')
        >>> b.markdown
        '[Object](base.Object)'
        >>> list(b)
        [Type('[Object](base.Object)')]
        >>> a.copy()
        Type('str')
    """

    markdown: str = field(default="", init=False)

    def __post_init__(self):
        if LINK_PATTERN.search(self.name):
            self.markdown = self.name
        else:
            self.html = self.name


@dataclass
class Item(Type):
    """Item class represents an item in Parameters, Attributes, and Raises sections,
    *etc.*

    Args:
        type: Type of self.
        description: Description of self.
        kind: Kind of self, for example `readonly property`. This value is rendered
            as a class attribute in HTML.

    Examples:
        >>> item = Item('[x](x)', Type('int'), Inline('A parameter.'))
        >>> item
        Item('[x](x)', 'int')
        >>> item.name, item.markdown, item.html
        ('[x](x)', '[x](x)', '')
        >>> item.type
        Type('int')
        >>> item.description
        Inline('A parameter.')
        >>> item = Item('[x](x)', 'str', 'A parameter.')
        >>> item.type
        Type('str')
        >>> it = iter(item)
        >>> next(it) is item
        True
        >>> next(it) is item.description
        True
        >>> item.set_html('<p><strong>init</strong></p>')
        >>> item.html
        '__init__'
    """

    markdown: str = field(default="", init=False)
    type: Type = field(default_factory=Type)
    description: Inline = field(default_factory=Inline)
    kind: str = ""

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = Type(self.type)
        if isinstance(self.description, str):
            self.description = Inline(self.description)
        super().__post_init__()

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r}, {self.type.name!r})"

    def __iter__(self) -> Iterator[Base]:
        if self.markdown:
            yield self
        yield from self.type
        yield from self.description

    def set_html(self, html: str):
        html = html.replace("<strong>", "__").replace("</strong>", "__")
        super().set_html(html)

    def to_tuple(self) -> Tuple[str, str, str]:
        """Returns a tuple of (name, type, description).

        Examples:
            >>> item = Item('[x](x)', 'int', 'A parameter.')
            >>> item.to_tuple()
            ('[x](x)', 'int', 'A parameter.')
        """
        return self.name, self.type.name, self.description.name

    def set_type(self, type: Type, force: bool = False):
        """Sets type.

        Args:
            item: Type instance.
            force: If True, overwrite self regardless of existing type and
                description.

        See Also:
            * Item.update_
        """
        if not force and self.type.name:
            return
        if type.name:
            self.type = type.copy()

    def set_description(self, description: Inline, force: bool = False):
        """Sets description.

        Args:
            description: Inline instance.
            force: If True, overwrite self regardless of existing type and
                description.

        See Also:
            * Item.update_
        """
        if not force and self.description.name:
            return
        if description.name:
            self.description = description.copy()

    def update(self, item: "Item", force: bool = False):
        """Updates type and description.

        Args:
            item: Item instance.
            force: If True, overwrite self regardless of existing type and
                description.

        Examples:
            >>> item = Item('x')
            >>> item2 = Item('x', 'int', 'description')
            >>> item.update(item2)
            >>> item.to_tuple()
            ('x', 'int', 'description')
            >>> item2 = Item('x', 'str', 'new description')
            >>> item.update(item2)
            >>> item.to_tuple()
            ('x', 'int', 'description')
            >>> item.update(item2, force=True)
            >>> item.to_tuple()
            ('x', 'str', 'new description')
            >>> item.update(Item('x'), force=True)
            >>> item.to_tuple()
            ('x', 'str', 'new description')
        """
        if item.name != self.name:
            raise ValueError(f"Different name: {self.name} != {item.name}.")
        self.set_description(item.description, force)
        self.set_type(item.type, force)

    def copy(self):
        return Item(*self.to_tuple(), kind=self.kind)


@dataclass
class Section(Base):
    """Section class represents a section in docstring.

    Args:
        items: List for Arguments, Attributes, or Raises sections, *etc.*
        type: Type of self.

    Examples:
        >>> items = [Item('x'), Item('[y](a)'), Item('z')]
        >>> section = Section('Parameters', items=items)
        >>> section
        Section('Parameters', num_items=3)
        >>> list(section)
        [Item('[y](a)', '')]
    """

    items: List[Item] = field(default_factory=list)
    type: Type = field(default_factory=Type)

    def __post_init__(self):
        if self.markdown:
            self.markdown = preprocess.convert(self.markdown)

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r}, num_items={len(self.items)})"

    def __bool__(self):
        """Returns True if the number of items is larger than 0."""
        return len(self.items) > 0

    def __iter__(self) -> Iterator[Base]:
        """Yields a Base_ instance that has non empty Markdown."""
        yield from self.type
        if self.markdown:
            yield self
        for item in self.items:
            yield from item

    def __getitem__(self, name: str) -> Item:
        """Returns an Item_ instance whose name is equal to `name`.

        If there is no Item instance, a Item instance is newly created.

        Args:
            name: Item name.

        Examples:
            >>> section = Section("", items=[Item('x')])
            >>> section['x']
            Item('x', '')
            >>> section['y']
            Item('y', '')
            >>> section.items
            [Item('x', ''), Item('y', '')]
        """
        for item in self.items:
            if item.name == name:
                return item
        item = Item(name)
        self.items.append(item)
        return item

    def __delitem__(self, name: str):
        """Delete an Item_ instance whose name is equal to `name`.

        Args:
            name: Item name.
        """
        for k, item in enumerate(self.items):
            if item.name == name:
                del self.items[k]
                return
        raise KeyError(f"name not found: {name}")

    def __contains__(self, name: str) -> bool:
        """Returns True if there is an [Item]() instance whose name is equal to `name`.

        Args:
            name: Item name.
        """
        for item in self.items:
            if item.name == name:
                return True
        return False

    def set_item(self, item: Item, force: bool = False):
        """Sets an [Item]().

        Args:
            item: Item instance.
            force: If True, overwrite self regardless of existing item.

        Examples:
            >>> items = [Item('x', 'int'), Item('y', 'str', 'y')]
            >>> section = Section('Parameters', items=items)
            >>> section.set_item(Item('x', 'float', 'X'))
            >>> section['x'].to_tuple()
            ('x', 'int', 'X')
            >>> section.set_item(Item('y', 'int', 'Y'), force=True)
            >>> section['y'].to_tuple()
            ('y', 'int', 'Y')
            >>> section.set_item(Item('z', 'float', 'Z'))
            >>> [item.name for item in section.items]
            ['x', 'y', 'z']

        See Also:
            * Section.update_
        """
        for k, x in enumerate(self.items):
            if x.name == item.name:
                self.items[k].update(item, force)
                return
        self.items.append(item.copy())

    def update(self, section: "Section", force: bool = False):
        """Updates items.

        Args:
            section: Section instance.
            force: If True, overwrite items of self regardless of existing value.

        Examples:
            >>> s1 = Section('Parameters', items=[Item('a', 's'), Item('b', 'f')])
            >>> s2 = Section('Parameters', items=[Item('a', 'i', 'A'), Item('x', 'd')])
            >>> s1.update(s2)
            >>> s1['a'].to_tuple()
            ('a', 's', 'A')
            >>> s1['x'].to_tuple()
            ('x', 'd', '')
            >>> s1.update(s2, force=True)
            >>> s1['a'].to_tuple()
            ('a', 'i', 'A')
            >>> s1.items
            [Item('a', 'i'), Item('b', 'f'), Item('x', 'd')]
        """
        for item in section.items:
            self.set_item(item, force)

    def merge(self, section: "Section", force: bool = False) -> "Section":
        """Returns a merged Section

        Examples:
            >>> s1 = Section('Parameters', items=[Item('a', 's'), Item('b', 'f')])
            >>> s2 = Section('Parameters', items=[Item('a', 'i'), Item('c', 'd')])
            >>> s3 = s1.merge(s2)
            >>> s3.items
            [Item('a', 's'), Item('b', 'f'), Item('c', 'd')]
            >>> s3 = s1.merge(s2, force=True)
            >>> s3.items
            [Item('a', 'i'), Item('b', 'f'), Item('c', 'd')]
            >>> s3 = s2.merge(s1)
            >>> s3.items
            [Item('a', 'i'), Item('c', 'd'), Item('b', 'f')]
        """
        if section.name != self.name:
            raise ValueError(f"Different name: {self.name} != {section.name}.")
        merged = Section(self.name)
        for item in self.items:
            merged.set_item(item)
        for item in section.items:
            merged.set_item(item, force=force)
        return merged

    def copy(self):
        """Returns a copy of the {class} instace.

        Examples:
            >>> s = Section('E', 'markdown', [Item('a', 's'), Item('b', 'i')])
            >>> s.copy()
            Section('E', num_items=2)
        """
        items = [item.copy() for item in self.items]
        return self.__class__(self.name, self.markdown, items=items)


SECTION_ORDER = ["Bases", "", "Parameters", "Attributes", "Returns", "Yields", "Raises"]


@dataclass
class Docstring:
    """Docstring class represents a docstring of an object.

    Args:
        sections: List of Section instance.
        type: Type for Returns or Yields sections.

    Examples:
        Empty docstring:
        >>> docstring = Docstring()
        >>> assert not docstring

        Docstring with 3 sections:
        >>> default = Section("", markdown="Default")
        >>> parameters = Section("Parameters", items=[Item("a"), Item("[b](!a)")])
        >>> returns = Section("Returns", markdown="Results")
        >>> docstring = Docstring([default, parameters, returns])
        >>> docstring
        Docstring(num_sections=3)

        `Docstring` is iterable:
        >>> list(docstring)
        [Section('', num_items=0), Item('[b](!a)', ''), Section('Returns', num_items=0)]

        Indexing:
        >>> docstring["Parameters"].items[0].name
        'a'

        Section ordering:
        >>> docstring = Docstring()
        >>> _ = docstring['']
        >>> _ = docstring['Todo']
        >>> _ = docstring['Attributes']
        >>> _ = docstring['Parameters']
        >>> [section.name for section in docstring.sections]
        ['', 'Parameters', 'Attributes', 'Todo']
    """

    sections: List[Section] = field(default_factory=list)
    type: Type = field(default_factory=Type)

    def __repr__(self):
        class_name = self.__class__.__name__
        num_sections = len(self.sections)
        return f"{class_name}(num_sections={num_sections})"

    def __bool__(self):
        """Returns True if the number of sections is larger than 0."""
        return len(self.sections) > 0

    def __iter__(self) -> Iterator[Base]:
        """Yields [Base]() instance."""
        for section in self.sections:
            yield from section

    def __getitem__(self, name: str) -> Section:
        """Returns a [Section]() instance whose name is equal to `name`.

        If there is no Section instance, a Section instance is newly created.

        Args:
            name: Section name.
        """
        for section in self.sections:
            if section.name == name:
                return section
        section = Section(name)
        self.set_section(section)
        return section

    def __contains__(self, name) -> bool:
        """Returns True if there is a [Section]() instance whose name is
        equal to `name`.

        Args:
            name: Section name.
        """
        for section in self.sections:
            if section.name == name:
                return True
        return False

    def set_section(
        self,
        section: Section,
        force: bool = False,
        copy: bool = False,
        replace: bool = False,
    ):
        """Sets a [Section]().

        Args:
            section: Section instance.
            force: If True, overwrite self regardless of existing seciton.

        Examples:
            >>> items = [Item('x', 'int'), Item('y', 'str', 'y')]
            >>> s1 = Section('Attributes', items=items)
            >>> items = [Item('x', 'str', 'X'), Item('z', 'str', 'z')]
            >>> s2 = Section('Attributes', items=items)
            >>> doc = Docstring([s1])
            >>> doc.set_section(s2)
            >>> doc['Attributes']['x'].to_tuple()
            ('x', 'int', 'X')
            >>> doc['Attributes']['z'].to_tuple()
            ('z', 'str', 'z')
            >>> doc.set_section(s2, force=True)
            >>> doc['Attributes']['x'].to_tuple()
            ('x', 'str', 'X')
            >>> items = [Item('x', 'X', 'str'), Item('z', 'z', 'str')]
            >>> s3 = Section('Parameters', items=items)
            >>> doc.set_section(s3)
            >>> doc.sections
            [Section('Parameters', num_items=2), Section('Attributes', num_items=3)]
        """
        name = section.name
        for k, x in enumerate(self.sections):
            if x.name == name:
                if replace:
                    self.sections[k] = section
                else:
                    self.sections[k].update(section, force=force)
                return
        if copy:
            section = section.copy()
        if name not in SECTION_ORDER:
            self.sections.append(section)
            return
        order = SECTION_ORDER.index(name)
        for k, x in enumerate(self.sections):
            if x.name not in SECTION_ORDER:
                self.sections.insert(k, section)
                return
            order_ = SECTION_ORDER.index(x.name)
            if order < order_:
                self.sections.insert(k, section)
                return
        self.sections.append(section)
