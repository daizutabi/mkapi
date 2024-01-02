"""Docstring module."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Self

from mkapi.utils import (
    add_admonition,
    add_fence,
    delete_ptags,
    get_indent,
    join_without_indent,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

LINK_PATTERN = re.compile(r"\[(.+?)\]\[(.+?)\]")

SECTION_NAMES = [
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
type Style = Literal["google", "numpy", ""]


@dataclass
class Base:
    """Base class.

    Examples:
        >>> base = Base("x", "markdown")
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

    name: str = ""
    markdown: str = ""
    html: str = field(default="", init=False)
    callback: Callable[[Self], str] | None = field(default=None, init=False)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r})"

    def __bool__(self) -> bool:
        """Return True if name is not empty."""
        return bool(self.name)

    def __iter__(self) -> Iterator[Self]:
        """Yield self if markdown is not empty."""
        if self.markdown:
            yield self

    def set_html(self, html: str) -> None:
        """Set HTML."""
        self.html = html
        if self.callback:
            self.html = self.callback(self)

    def copy(self) -> Self:
        """Return a copy of the instance."""
        return self.__class__(name=self.name, markdown=self.markdown)


@dataclass(repr=False)
class Inline(Base):
    """Inline class.

    Examples:
        >>> inline = Inline()
        >>> bool(inline)
        False
        >>> inline = Inline("markdown")
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

    def __post_init__(self) -> None:
        self.markdown = self.name

    def set_html(self, html: str) -> None:
        """Set `html` attribute cleaning `p` tags."""
        html = delete_ptags(html)
        super().set_html(html)

    def copy(self) -> Self:  # noqa: D102
        return self.__class__(name=self.name)


@dataclass(repr=False)
class Type(Inline):
    """Type of [Item], [Section], [Docstring], or [Object].

    Examples:
        >>> a = Type("str")
        >>> a
        Type('str')
        >>> list(a)
        []
        >>> b = Type("[Base][docstring.Base]")
        >>> b.markdown
        '[Base][docstring.Base]'
        >>> list(b)
        [Type('[Base][docstring.Base]')]
        >>> a.copy()
        Type('str')
    """

    markdown: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if LINK_PATTERN.search(self.name):
            self.markdown = self.name
        else:
            self.html = self.name


@dataclass
class Item(Type):
    """Item in Parameters, Attributes, and Raises sections, *etc.*.

    Args:
        type: Type of self.
        description: Description of self.
        kind: Kind of self, for example `readonly property`. This value is rendered
            as a class attribute in HTML.

    Examples:
        >>> item = Item('[x][x]', Type('int'), Inline('A parameter.'))
        >>> item
        Item('[x][x]', 'int')
        >>> item.name, item.markdown, item.html
        ('[x][x]', '[x][x]', '')
        >>> item.type
        Type('int')
        >>> item.description
        Inline('A parameter.')
        >>> item = Item('[x][x]', 'str', 'A parameter.')
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
    type: Type = field(default_factory=Type)  # noqa: A003
    description: Inline = field(default_factory=Inline)
    kind: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            self.type = Type(self.type)
        if isinstance(self.description, str):
            self.description = Inline(self.description)
        super().__post_init__()

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r}, {self.type.name!r})"

    def __iter__(self) -> Iterator[Base]:
        if self.markdown:
            yield self
        yield from self.type
        yield from self.description

    def set_html(self, html: str) -> None:
        """Set `html` attribute cleaning `strong` tags."""
        html = html.replace("<strong>", "__").replace("</strong>", "__")
        super().set_html(html)

    def to_tuple(self) -> tuple[str, str, str]:
        """Return a tuple of (name, type, description).

        Examples:
            >>> item = Item("[x][x]", "int", "A parameter.")
            >>> item.to_tuple()
            ('[x][x]', 'int', 'A parameter.')
        """
        return self.name, self.type.name, self.description.name

    def set_type(self, type_: Type, *, force: bool = False) -> None:
        """Set type.

        Args:
            type_: Type instance.
            force: If True, overwrite self regardless of existing type and
                description.

        See Also:
            * [Item.update]
        """
        if not force and self.type.name:
            return
        if type_.name:
            self.type = type_.copy()

    def set_description(self, description: Inline, *, force: bool = False) -> None:
        """Set description.

        Args:
            description: Inline instance.
            force: If True, overwrite self regardless of existing type and
                description.

        See Also:
            * [Item.update]
        """
        if not force and self.description.name:
            return
        if description.name:
            self.description = description.copy()

    def update(self, item: Item, *, force: bool = False) -> None:
        """Update type and description.

        Args:
            item: Item instance.
            force: If True, overwrite self regardless of existing type and
                description.

        Examples:
            >>> item = Item("x")
            >>> item2 = Item("x", "int", "description")
            >>> item.update(item2)
            >>> item.to_tuple()
            ('x', 'int', 'description')
            >>> item2 = Item("x", "str", "new description")
            >>> item.update(item2)
            >>> item.to_tuple()
            ('x', 'int', 'description')
            >>> item.update(item2, force=True)
            >>> item.to_tuple()
            ('x', 'str', 'new description')
            >>> item.update(Item("x"), force=True)
            >>> item.to_tuple()
            ('x', 'str', 'new description')
        """
        if item.name != self.name:
            msg = f"Different name: {self.name} != {item.name}."
            raise ValueError(msg)
        self.set_description(item.description, force=force)
        self.set_type(item.type, force=force)

    def copy(self) -> Self:  # noqa: D102
        name, type_, desc = self.to_tuple()
        return self.__class__(name, Type(type_), Inline(desc), kind=self.kind)


@dataclass
class Section(Base):
    """Section in docstring.

    Args:
        items: List for Arguments, Attributes, or Raises sections, *etc.*
        type: Type of self.

    Examples:
        >>> items = [Item("x"), Item("[y][a]"), Item("z")]
        >>> section = Section("Parameters", items=items)
        >>> section
        Section('Parameters', num_items=3)
        >>> list(section)
        [Item('[y][a]', '')]
    """

    items: list[Item] = field(default_factory=list)
    type: Type = field(default_factory=Type)  # noqa: A003

    def __post_init__(self) -> None:
        if self.markdown:
            self.markdown = add_fence(self.markdown)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r}, num_items={len(self.items)})"

    def __bool__(self) -> bool:
        """Return True if the number of items is larger than 0."""
        return len(self.items) > 0

    def __iter__(self) -> Iterator[Base]:
        """Yield a Base_ instance that has non empty Markdown."""
        yield from self.type
        if self.markdown:
            yield self
        for item in self.items:
            yield from item

    def __getitem__(self, name: str) -> Item:
        """Return an Item_ instance whose name is equal to `name`.

        If there is no Item instance, a Item instance is newly created.

        Args:
            name: Item name.

        Examples:
            >>> section = Section("", items=[Item("x")])
            >>> section["x"]
            Item('x', '')
            >>> section["y"]
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

    def __delitem__(self, name: str) -> None:
        """Delete an Item_ instance whose name is equal to `name`.

        Args:
            name: Item name.
        """
        for k, item in enumerate(self.items):
            if item.name == name:
                del self.items[k]
                return
        msg = f"name not found: {name}"
        raise KeyError(msg)

    def __contains__(self, name: str) -> bool:
        """Return True if there is an [Item] instance whose name is equal to `name`.

        Args:
            name: Item name.
        """
        return any(item.name == name for item in self.items)

    def set_item(self, item: Item, *, force: bool = False) -> None:
        """Set an [Item].

        Args:
            item: Item instance.
            force: If True, overwrite self regardless of existing item.

        Examples:
            >>> items = [Item("x", "int"), Item("y", "str", "y")]
            >>> section = Section("Parameters", items=items)
            >>> section.set_item(Item("x", "float", "X"))
            >>> section["x"].to_tuple()
            ('x', 'int', 'X')
            >>> section.set_item(Item("y", "int", "Y"), force=True)
            >>> section["y"].to_tuple()
            ('y', 'int', 'Y')
            >>> section.set_item(Item("z", "float", "Z"))
            >>> [item.name for item in section.items]
            ['x', 'y', 'z']

        See Also:
            * Section.update_
        """
        for k, x in enumerate(self.items):
            if x.name == item.name:
                self.items[k].update(item, force=force)
                return
        self.items.append(item.copy())

    def update(self, section: Section, *, force: bool = False) -> None:
        """Update items.

        Args:
            section: Section instance.
            force: If True, overwrite items of self regardless of existing value.

        Examples:
            >>> s1 = Section("Parameters", items=[Item("a", "s"), Item("b", "f")])
            >>> s2 = Section("Parameters", items=[Item("a", "i", "A"), Item("x", "d")])
            >>> s1.update(s2)
            >>> s1["a"].to_tuple()
            ('a', 's', 'A')
            >>> s1["x"].to_tuple()
            ('x', 'd', '')
            >>> s1.update(s2, force=True)
            >>> s1["a"].to_tuple()
            ('a', 'i', 'A')
            >>> s1.items
            [Item('a', 'i'), Item('b', 'f'), Item('x', 'd')]
        """
        for item in section.items:
            self.set_item(item, force=force)

    def merge(self, section: Section, *, force: bool = False) -> Section:
        """Return a merged Section.

        Examples:
            >>> s1 = Section("Parameters", items=[Item("a", "s"), Item("b", "f")])
            >>> s2 = Section("Parameters", items=[Item("a", "i"), Item("c", "d")])
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
            msg = f"Different name: {self.name} != {section.name}."
            raise ValueError(msg)
        merged = Section(self.name)
        for item in self.items:
            merged.set_item(item)
        for item in section.items:
            merged.set_item(item, force=force)
        return merged

    def copy(self) -> Self:
        """Return a copy of the instace.

        Examples:
            >>> s = Section("E", "markdown", [Item("a", "s"), Item("b", "i")])
            >>> s.copy()
            Section('E', num_items=2)
        """
        items = [item.copy() for item in self.items]
        return self.__class__(self.name, self.markdown, items=items)


SECTION_ORDER = ["Bases", "", "Parameters", "Attributes", "Returns", "Yields", "Raises"]


@dataclass
class Docstring:
    """Docstring of an object.

    Args:
        sections: List of [Section] instance.
        type: [Type] for Returns or Yields sections.

    Examples:
        Empty docstring:
        >>> docstring = Docstring()
        >>> assert not docstring

        Docstring with 3 sections:
        >>> default = Section("", markdown="Default")
        >>> parameters = Section("Parameters", items=[Item("a"), Item("[b][!a]")])
        >>> returns = Section("Returns", markdown="Results")
        >>> docstring = Docstring([default, parameters, returns])
        >>> docstring
        Docstring(num_sections=3)

        `Docstring` is iterable:
        >>> list(docstring)
        [Section('', num_items=0), Item('[b][!a]', ''), Section('Returns', num_items=0)]

        Indexing:
        >>> docstring["Parameters"].items[0].name
        'a'

        Section ordering:
        >>> docstring = Docstring()
        >>> _ = docstring[""]
        >>> _ = docstring["Todo"]
        >>> _ = docstring["Attributes"]
        >>> _ = docstring["Parameters"]
        >>> [section.name for section in docstring.sections]
        ['', 'Parameters', 'Attributes', 'Todo']
    """

    sections: list[Section] = field(default_factory=list)
    type: Type = field(default_factory=Type)  # noqa: A003

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        num_sections = len(self.sections)
        return f"{class_name}(num_sections={num_sections})"

    def __bool__(self) -> bool:
        """Return True if the number of sections is larger than 0."""
        return len(self.sections) > 0

    def __iter__(self) -> Iterator[Base]:
        """Yield [Base]() instance."""
        for section in self.sections:
            yield from section

    def __getitem__(self, name: str) -> Section:
        """Return a [Section]() instance whose name is equal to `name`.

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

    def __contains__(self, name: str) -> bool:
        """Return True if there is a [Section]() instance whose name is equal to `name`.

        Args:
            name: Section name.
        """
        return any(section.name == name for section in self.sections)

    def set_section(
        self,
        section: Section,
        *,
        force: bool = False,
        copy: bool = False,
        replace: bool = False,
    ) -> None:
        """Set a [Section].

        Args:
            section: Section instance.
            force: If True, overwrite self regardless of existing seciton.
            copy: If True, section is copied.
            replace: If True,section is replaced.

        Examples:
            >>> items = [Item("x", "int"), Item("y", "str", "y")]
            >>> s1 = Section('Attributes', items=items)
            >>> items = [Item("x", "str", "X"), Item("z", "str", "z")]
            >>> s2 = Section("Attributes", items=items)
            >>> doc = Docstring([s1])
            >>> doc.set_section(s2)
            >>> doc["Attributes"]["x"].to_tuple()
            ('x', 'int', 'X')
            >>> doc["Attributes"]["z"].to_tuple()
            ('z', 'str', 'z')
            >>> doc.set_section(s2, force=True)
            >>> doc["Attributes"]["x"].to_tuple()
            ('x', 'str', 'X')
            >>> items = [Item("x", "X", "str"), Item("z", "z", "str")]
            >>> s3 = Section("Parameters", items=items)
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


def _rename_section(name: str) -> str:
    if name in ["Args", "Arguments"]:
        return "Parameters"
    if name == "Warns":
        return "Warnings"
    return name


def section_heading(line: str) -> tuple[str, Style]:
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
    if line in SECTION_NAMES:
        return line, "numpy"
    if line.endswith(":") and line[:-1] in SECTION_NAMES:
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
                style, start, name = style_, stop, _rename_section(section)
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
    """Return a [Item] instance corresponding to a parameter.

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


def parse_section(name: str, doc: str, style: str) -> Section:
    """Return a [Section] instance."""
    type_ = markdown = ""
    items = []
    if name in ["Parameters", "Attributes", "Raises"]:
        items = parse_parameters(doc, style)
    elif name in ["Returns", "Yields"]:
        type_, markdown = parse_returns(doc, style)
    else:
        markdown = doc
    return Section(name, markdown, items, Type(type_))


def postprocess_sections(sections: list[Section]) -> None:  # noqa: D103
    for section in sections:
        if section.name in ["Note", "Notes", "Warning", "Warnings"]:
            markdown = add_admonition(section.name, section.markdown)
            if sections and sections[-1].name == "":
                sections[-1].markdown += "\n\n" + markdown
                continue
            section.name = ""
            section.markdown = markdown


def parse_docstring(doc: str) -> Docstring:
    """Return a [Docstring]) instance."""
    if not doc:
        return Docstring()
    sections = [parse_section(*section_args) for section_args in split_section(doc)]
    postprocess_sections(sections)
    return Docstring(sections)


# def parse_bases(doc: Docstring, obj: object) -> None:
#     """Parse base classes to create a Base(s) line."""
#     if not inspect.isclass(obj) or not hasattr(obj, "mro"):
#         return
#     objs = get_mro(obj)[1:]
#     if not objs:
#         return
#     types = [get_link(obj_, include_module=True) for obj_ in objs]
#     items = [Item(type=Type(type_)) for type_ in types if type_]
#     doc.set_section(Section("Bases", items=items))


# def parse_source(doc: Docstring, obj: object) -> None:
#     """Parse parameters' docstring to inspect type and description from source.

#     Examples:
#         >>> from mkapi.core.base import Base
#         >>> doc = Docstring()
#         >>> parse_source(doc, Base)
#         >>> section = doc["Parameters"]
#         >>> section["name"].to_tuple()
#         ('name', 'str, optional', 'Name of self.')
#         >>> section = doc["Attributes"]
#         >>> section["html"].to_tuple()
#         ('html', 'str', 'HTML output after conversion.')
#     """
#     signature = get_signature(obj)
#     name = "Parameters"
#     section: Section = signature[name]
#     if name in doc:
#         section = section.merge(doc[name], force=True)
#     if section:
#         doc.set_section(section, replace=True)

#     name = "Attributes"
#     section: Section = signature[name]
#     if name not in doc and not section:
#         return
#     doc[name].update(section)
#     if is_dataclass(obj) and "Parameters" in doc:
#         for item in doc["Parameters"].items:
#             if item.name in section:
#                 doc[name].set_item(item)


# def postprocess_parameters(doc: Docstring, signature: Signature) -> None:
#     if "Parameters" not in doc:
#         return
#     for item in doc["Parameters"].items:
#         description = item.description
#         if "{default}" in description.name and item.name in signature:
#             default = signature.defaults[item.name]
#             description.markdown = description.name.replace("{default}", default)


# def postprocess_returns(doc: Docstring, signature: Signature) -> None:
#     for name in ["Returns", "Yields"]:
#         if name in doc:
#             section = doc[name]
#             if not section.type:
#                 section.type = Type(getattr(signature, name.lower()))


# def postprocess_sections(doc: Docstring, obj: object) -> None:
#     sections: list[Section] = []
#     for section in doc.sections:
#         if section.name not in ["Example", "Examples"]:
#             for base in section:
#                 base.markdown = replace_link(obj, base.markdown)
#         if section.name in ["Note", "Notes", "Warning", "Warnings"]:
#             markdown = add_admonition(section.name, section.markdown)
#             if sections and sections[-1].name == "":
#                 sections[-1].markdown += "\n\n" + markdown
#                 continue
#             section.name = ""
#             section.markdown = markdown
#         sections.append(section)
#     doc.sections = sections


# def set_docstring_type(doc: Docstring, signature: Signature, obj: object) -> None:
#     from mkapi.core.node import get_kind

#     if "Returns" not in doc and "Yields" not in doc:
#         if get_kind(obj) == "generator":
#             doc.type = Type(signature.yields)
#         else:
#             doc.type = Type(signature.returns)


# def postprocess_docstring(doc: Docstring, obj: object) -> None:
#     """Docstring prostprocess."""
#     parse_bases(doc, obj)
#     parse_source(doc, obj)

#     if not callable(obj):
#         return

#     signature = get_signature(obj)
#     if not signature.signature:
#         return

#     postprocess_parameters(doc, signature)
#     postprocess_returns(doc, signature)
#     postprocess_sections(doc, obj)
#     set_docstring_type(doc, signature, obj)


# def get_docstring(obj: object) -> Docstring:
#     """Return a [Docstring]) instance."""
#     doc = inspect.getdoc(obj)
#     if not doc:
#         return Docstring()
#     sections = [get_section(*section_args) for section_args in split_section(doc)]
#     docstring = Docstring(sections)
#     postprocess_docstring(docstring, obj)
#     return docstring
