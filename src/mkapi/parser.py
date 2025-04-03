"""Parsing and managing Python objects for documentation generation.

Provide the `Parser` class, which is responsible for parsing various
Python objects such as modules, classes, functions, and attributes.
Facilitate the extraction of structured information from these objects
to generate comprehensive documentation.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from inspect import _ParameterKind as P
from typing import TYPE_CHECKING, TypeAlias

import astdoc.ast
import astdoc.markdown
import astdoc.object
from astdoc.doc import Doc, Item, Section
from astdoc.node import (
    get_fullname_from_module,
    iter_classes_from_module,
    iter_functions_from_module,
    iter_methods_from_class,
    iter_modules_from_module,
)
from astdoc.object import (
    Attribute,
    Class,
    Function,
    Module,
    Property,
    Type,
    get_fullname_from_object,
    get_object,
)
from astdoc.utils import (
    find_item_by_name,
    find_submodule_names,
    is_enum,
    is_identifier,
    is_package,
    iter_attribute_names,
    iter_identifiers,
    split_module_name,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from astdoc.ast import Parameter


@dataclass
class NameSet:
    """Represent a name set."""

    kind: str
    name: str
    parent: str | None
    module: str | None
    fullname: str
    id: str
    obj_id: str
    parent_id: str | None


@dataclass
class Parser:
    """Parse and manage Python objects for documentation generation.

    Provide methods to create a parser instance from a given name,
    retrieve the full name of objects, and parse various components of the
    documentation, including name sets, signatures, bases, and the first paragraph
    of the docstring. It also facilitates the merging of documentation sections
    for a comprehensive output.
    """

    name: str
    """The name of the object to parse."""

    module: str | None
    """The module of the object to parse."""

    obj: Attribute | Class | Function | Module | Property
    """The object to parse."""

    @classmethod
    def create(cls, name: str, module: str | None = None) -> Parser | None:
        """Create a `Parser` instance from a given name.

        Args:
            name (str): The name of the object to parse.
            module (str | None): The module of the object to parse.

        Returns:
            Parser | None: A `Parser` instance if the object is valid,
            otherwise None.

        """
        if not module:
            if not (name_module := split_module_name(name)):
                return None

            name, module = name_module

        obj = get_object(name, module)

        if not isinstance(obj, Attribute | Class | Function | Module | Property):
            return None

        return cls(name, module, obj)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self.module!r})"

    def replace_from_module(self, name: str) -> str | None:
        """Replace the name with the full name from the module.

        Args:
            name (str): The name to replace.

        Returns:
            str | None: The full name if the name is valid, otherwise None.

        """
        module = self.obj.module or self.obj.name
        return get_fullname_from_module(name, module)

    def replace_from_object(self, name: str) -> str | None:
        """Replace the name with the full name from the object.

        Args:
            name (str): The name to replace.

        Returns:
            str | None: The full name if the name is valid, otherwise None.

        """
        return get_fullname_from_object(name, self.obj)

    def parse_name_set(self) -> NameSet:
        """Parse the name set.

        Returns:
            NameSet: The name set.

        """
        qualname = self.name.replace("_", "\\_")
        obj_id = self.obj.fullname
        parent = None
        parent_id = None

        if self.module:
            module = self.module.replace("_", "\\_")
            fullname = f"{module}.{qualname}"
            id_ = f"{self.module}.{self.name}"

            if "." in qualname:
                parent, name = qualname.rsplit(".", 1)
                parent_id = id_.rsplit(".", 1)[0]
            else:
                name = qualname

        else:
            name = fullname = qualname
            module = None
            id_ = self.name

        kind = self.obj.kind.replace("async function", "async")
        kind = kind.replace("function", "")

        return NameSet(
            kind,
            name,
            parent,
            module,
            fullname,
            id_,
            obj_id,
            parent_id,
        )

    def parse_signature(self) -> list[tuple[str, str]]:
        """Parse the signature.

        Returns:
            list[tuple[str, str]]: The signature.

        """
        if isinstance(self.obj, Module):
            return []

        signatures = []
        for part in get_signature(self.obj):
            if isinstance(part.name, ast.expr):
                name = get_markdown_expr(
                    part.name,
                    self.replace_from_module,
                    is_type=False,
                )

            elif part._kind in [PartKind.ANN, PartKind.RETURN]:  # noqa: SLF001
                name = get_markdown_str(part.name, self.replace_from_module)

            else:
                name = part.name

            signatures.append((name, part.kind))

        return signatures

    def parse_bases(self) -> list[str]:
        """Parse the base classes.

        Returns:
            list[str]: The base classes.

        """
        if not isinstance(self.obj, Class):
            return []

        bases = []
        for base in self.obj.node.bases:
            name = get_markdown_expr(base, self.replace_from_module)
            bases.append(name)

        return bases

    def parse_summary(self) -> str:
        """Parse the summary.

        Returns:
            str: The summary.

        """
        summary = self.obj.doc.text.split("\n\n", maxsplit=1)[0]
        return get_markdown_text(summary, self.replace_from_object)

    def parse_doc(self) -> Doc:
        """Parse the doc.

        The doc is cloned and modified in the following ways:

        - Merge sections
        - Set markdown
        - Add summary sections from the first paragraph

        Returns:
            Doc: The doc.

        """
        doc = self.obj.doc.clone()
        merge_sections(doc.sections, self.obj)
        set_markdown_doc(doc, self.replace_from_object)
        doc.sections.extend(self._iter_summary_sections())
        return doc

    def _iter_summary_sections(self) -> Iterator[Section]:
        if isinstance(self.obj, Module):
            created = False

            if section := create_classes_from_module(self.name):
                created = True
                yield section

            if section := create_functions_from_module(self.name):
                created = True
                yield section

            if section := create_modules_from_module(self.name):
                created = True
                yield section

            elif not created and (
                section := create_modules_from_module_file(self.name)
            ):
                yield section

        if isinstance(self.obj, Class) and self.module:
            if section := create_methods_from_class(self.name, self.module):
                yield section


PREFIX = "__mkapi__."


def get_markdown_link(name: str, ref: str | None, *, in_code: bool = False) -> str:
    """Return a Markdown link.

    Generate a Markdown formatted link for a given object name and its reference.
    It can format the link differently based on whether it is intended to be
    displayed in code or not.

    Args:
        name (str): The name of the object to link.
        ref (str | None): The reference of the object, which is used to
            create the link target.
        in_code (bool): Whether the link is in code. If True, the link will
            be formatted for inline code. Defaults to False.

    Returns:
        str: A Markdown formatted string that represents the link.

    Examples:
        >>> get_markdown_link("foo", "bar")
        '[foo][__mkapi__.bar]'
        >>> get_markdown_link("foo", "bar", in_code=True)
        '[`foo`][__mkapi__.bar]'

    """
    if not in_code:
        name = name.replace("_", "\\_")

    if in_code:
        return f"[`{name}`][{PREFIX}{ref}]" if ref else f"`{name}`"

    return f"[{name}][{PREFIX}{ref}]" if ref else name


Replace: TypeAlias = Callable[[str], str | None] | None


def get_markdown_name(fullname: str, replace: Replace = None) -> str:
    """Return a Markdown formatted string from the fullname.

    Take a fully qualified name (e.g., "foo.bar") and generate
    a Markdown formatted link for each component of the name.
    It splits the fullname into its constituent parts and creates links
    for each part using the `get_markdown_link` function.
    If a replacement function is provided, it will be applied to each
    reference before generating the links.

    Args:
        fullname (str): The fully qualified name of the object, formatted as
            a dot-separated string (e.g., "foo.bar").
        replace (Replace, optional): A function that takes a string and returns
            a modified string. This function is applied to each reference
            before generating the Markdown links. Defaults to None.

    Returns:
        str: A Markdown formatted string that represents the links for each
            component of the fullname.

    Examples:
        >>> get_markdown_name("foo.bar")
        '[foo][__mkapi__.foo].[bar][__mkapi__.foo.bar]'
        >>> get_markdown_name("foo.bar", lambda x: x.replace("bar", "baz"))
        '[foo][__mkapi__.foo].[bar][__mkapi__.foo.baz]'

    """
    names = fullname.split(".")
    refs = iter_attribute_names(fullname)

    if replace:
        refs = [replace(ref) for ref in refs]

    it = zip(names, refs, strict=True)
    return ".".join(get_markdown_link(*names) for names in it)


def get_markdown_str(type_str: str, replace: Replace = None) -> str:
    """Return a Markdown formatted string from the type string.

    Take a type string (e.g., "foo[bar]" or "foo, bar") and generate
    a Markdown formatted representation of the string.

    Args:
        type_str (str): The type string to be converted into Markdown format.
        replace (Replace, optional): A function that takes a string and returns
            a modified string. This function is applied to each reference
            before generating the Markdown links. Defaults to None.

    Returns:
        str: A Markdown formatted string that represents the type string with
            appropriate links for its components.

    Examples:
        >>> get_markdown_str("foo[bar]",None)
        '[foo][__mkapi__.foo][[bar][__mkapi__.bar]]'
        >>> get_markdown_str("foo, bar", lambda x: x.replace("bar", "baz"))
        '[foo][__mkapi__.foo], [bar][__mkapi__.baz]'

    """
    it = iter_identifiers(type_str)
    markdowns = (get_markdown_name(name, replace) if is_ else name for name, is_ in it)
    return "".join(markdowns)


def get_markdown_expr(
    expr: ast.expr,
    replace: Replace = None,
    *,
    is_type: bool = True,
) -> str:
    """Return a Markdown formatted string from an AST expression.

    Take an Abstract Syntax Tree (AST) expression and generate
    a Markdown formatted representation of the expression.
    It handles different types of expressions, such as constants
    and subscripted values.

    Args:
        expr (ast.expr): The AST expression to be converted into Markdown format.
        replace (Replace, optional): A function that takes a string and returns
            a modified string. This function is applied to each reference
            before generating the Markdown links. Defaults to None.
        is_type (bool): Whether the expression is a type. Defaults to True.

    Returns:
        str: A Markdown formatted string that represents the AST expression.

    Examples:
        >>> import ast
        >>> expr = ast.parse("foo[bar]").body[0].value
        >>> assert isinstance(expr, ast.Subscript)
        >>> get_markdown_expr(expr)
        '[foo][__mkapi__.foo][[bar][__mkapi__.bar]]'
        >>> get_markdown_expr(expr, lambda x: x.replace("bar", "baz"))
        '[foo][__mkapi__.foo][[bar][__mkapi__.baz]]'

    """
    if isinstance(expr, ast.Constant):
        value = expr.value

        if isinstance(value, str):
            return get_markdown_str(value, replace)

        return str(value)

    def get_link(name: str) -> str:
        return get_markdown_name(name, replace)

    try:
        return astdoc.ast.unparse(expr, get_link, is_type=is_type)
    except ValueError:
        return ast.unparse(expr)


def get_markdown_type(type_: str | ast.expr | None, replace: Replace) -> str:
    """Return a Markdown formatted string from a type or AST expression.

    Take a type, which can be a string, an AST expression, or None,
    and generate a Markdown formatted representation.
    If the input is None, it returns an empty string.

    Args:
        type_ (str | ast.expr | None): The type or AST expression to be converted
            into Markdown format. Can be a string, an AST expression, or None.
        replace (Replace): A function that takes a string and returns
            a modified string. This function is applied to each reference
            before generating the Markdown links.

    Returns:
        str: A Markdown formatted string representing the type or AST expression.
            Returns an empty string if the input is None.

    """
    if type_ is None:
        return ""

    if isinstance(type_, str):
        return get_markdown_str(type_, replace)

    return get_markdown_expr(type_, replace)


CODE_PATTERN = re.compile(r"(?P<pre>`+)(?P<name>.+?)(?P=pre)")


def get_markdown_text(text: str, replace: Replace) -> str:
    """Return a Markdown formatted string from the input text.

    Process the input text to convert specific patterns into
    Markdown formatted links. It uses a regular expression to identify code
    segments and applies a replacement function if provided.

    Args:
        text (str): The input text to be converted into Markdown format.
        replace (Replace): A function that takes a string and returns
            a modified string. This function is applied to each identifier
            before generating the Markdown links.

    Returns:
        str: A Markdown formatted string with appropriate links for identifiers.

    Examples:
        >>> get_markdown_text("Use `foo.bar`.", lambda x: x.replace("bar", "baz"))
        'Use [`foo.bar`][__mkapi__.foo.baz].'

    """

    def _replace(match: re.Match) -> str:
        if len(match.group("pre")) != 1:
            return match.group()

        name = match.group("name")

        if is_identifier(name) and replace and (ref := replace(name)):
            return get_markdown_link(name, ref, in_code=True)

        return match.group()

    return astdoc.markdown.sub(CODE_PATTERN, _replace, text)


def set_markdown_doc(doc: Doc, replace: Replace) -> None:
    """Set Markdown formatting for the given document.

    Update the text and type of the provided `Doc` object
    and its sections and items to be Markdown formatted.
    It uses the `get_markdown_text` and `get_markdown_type` functions
    to convert the text and type of the document, sections, and items.

    Args:
        doc (Doc): The document object to be updated with Markdown formatting.
        replace (Replace): A function that takes a string and returns
            a modified string. This function is applied to each identifier
            before generating the Markdown links.

    Returns:
        None: This function does not return a value; it modifies the `Doc`
        object in place.

    """
    doc.text = get_markdown_text(doc.text, replace)
    doc.type = get_markdown_type(doc.type, replace)

    for section in doc.sections:
        section.text = get_markdown_text(section.text, replace)
        section.type = get_markdown_type(section.type, replace)

        for item in section.items:
            item.name = item.name.replace("_", "\\_")
            item.text = get_markdown_text(item.text, replace)
            item.type = get_markdown_type(item.type, replace)


@dataclass
class Signature:
    """Represent a function or method signature, consisting of its parts.

    Encapsulate the individual components of a signature, allowing for
    easy access and iteration over the parts. Each part can represent different
    elements of the signature, such as parameters, return types, and other
    syntactical elements.
    """

    parts: list[Part]
    """A list of parts of the signature."""

    def __getitem__(self, index: int) -> Part:
        return self.parts[index]

    def __len__(self) -> int:
        return len(self.parts)

    def __iter__(self) -> Iterator[Part]:
        return iter(self.parts)


@dataclass
class Part:
    """Represent a part of the signature."""

    name: ast.expr | str
    """The name of the signature part."""

    _kind: PartKind
    """The kind of the signature part."""

    @property
    def kind(self) -> str:
        """The kind of the signature part as a string."""
        return self._kind.value


class PartKind(Enum):
    """Represent the kind of the signature part."""

    ANN = "ann"
    ARG = "arg"
    ARROW = "arrow"
    COLON = "colon"
    COMMA = "comma"
    DEFAULT = "default"
    EQUAL = "equal"
    PAREN = "paren"
    RETURN = "return"
    SLASH = "slash"
    STAR = "star"


def get_signature(obj: Class | Function | Attribute | Property) -> Signature:
    """Get the signature of the given object.

    Take an object, which can be a Class, Function, Attribute, or Property,
    and return its signature as a Signature object. The signature includes
    various parts such as parameters, return types, and other syntactical
    elements.

    Args:
        obj (Class | Function | Attribute | Property): The object
            whose signature is to be retrieved.

    Returns:
        Signature: The signature of the given object.

    """
    if isinstance(obj, Class | Function):
        parts = [Part(value, kind) for value, kind in _iter_signature(obj)]
        return Signature(parts)

    if obj.type:
        parts = [Part(": ", PartKind.COLON), Part(obj.type, PartKind.RETURN)]
        return Signature(parts)

    return Signature([])


def _iter_signature(
    obj: Class | Function,
) -> Iterator[tuple[ast.expr | str, PartKind]]:
    yield "(", PartKind.PAREN
    n = len(obj.parameters)
    prev_kind = None

    for k, param in enumerate(obj.parameters):
        if k == 0 and obj.kind in ["method", "classmethod"]:
            continue

        yield from _iter_sep(param.kind, prev_kind)

        yield param.name.replace("_", "\\_"), PartKind.ARG
        yield from _iter_param(param)

        if k < n - 1:
            yield ", ", PartKind.COMMA

        prev_kind = param.kind

    if prev_kind is P.POSITIONAL_ONLY:
        yield ", ", PartKind.COMMA
        yield "/", PartKind.SLASH

    yield ")", PartKind.PAREN

    if isinstance(obj, Class) or not obj.node.returns:
        return

    yield " → ", PartKind.ARROW
    yield obj.node.returns, PartKind.RETURN


def _iter_sep(kind: P | None, prev_kind: P | None) -> Iterator[tuple[str, PartKind]]:
    if prev_kind is P.POSITIONAL_ONLY and kind != prev_kind:
        yield "/", PartKind.SLASH
        yield ", ", PartKind.COMMA

    if kind is P.KEYWORD_ONLY and prev_kind not in [kind, P.VAR_POSITIONAL]:
        yield r"\*", PartKind.STAR
        yield ", ", PartKind.COMMA

    if kind is P.VAR_POSITIONAL:
        yield r"\*", PartKind.STAR

    if kind is P.VAR_KEYWORD:
        yield r"\*\*", PartKind.STAR


def _iter_param(param: Parameter) -> Iterator[tuple[ast.expr | str, PartKind]]:
    if param.type:
        yield ": ", PartKind.COLON
        yield param.type, PartKind.ANN

    if param.default:
        eq = " = " if param.type else "="
        yield eq, PartKind.EQUAL

        default = param.default
        if isinstance(default, ast.Constant) and isinstance(default.value, str):
            default = f"{default.value!r}"

        yield default, PartKind.DEFAULT


def merge_parameters(sections: list[Section], params: list[Parameter]) -> None:
    """Merge the parameters from the given sections and parameters list.

    Update the Parameters section of the documentation by merging the
    provided parameters list. If a parameter in the section does
    not have a type, it will be updated with the type from the parameters list.

    Args:
        sections (list[Section]): The list of documentation sections.
        params (list[Parameter]): The list of parameters to merge.

    Returns:
        None

    """
    if not (section := find_item_by_name(sections, "Parameters")):
        return

    for item in section.items:
        if item.type:
            continue

        name = item.name.replace("*", "")
        if param := find_item_by_name(params, name):
            item.type = param.type


def merge_raises(sections: list[Section], raises: list[ast.expr]) -> None:
    """Merge the raises from the given sections and raises list.

    Update the Raises section of the documentation by merging the
    provided raises list. If a raise in the section does
    not have a type, it will be updated with the type from the raises list.

    Args:
        sections (list[Section]): The list of documentation sections.
        raises (list[ast.expr]): The list of raises to merge.

    Returns:
        None

    """
    section = find_item_by_name(sections, "Raises")

    if not section:
        if not raises:
            return

        section = Section("Raises", "", "", [])
        sections.append(section)

    for raise_ in raises:
        if find_item_by_name(section.items, ast.unparse(raise_)):
            continue

        if find_item_by_name(section.items, ast.unparse(raise_), attr="type"):
            continue

        section.items.append(Item("", raise_, ""))


def merge_returns(
    sections: list[Section],
    returns: ast.expr | None,
    module: str,
) -> None:
    """Merge the return type from the given sections and returns expression.

    Update the Returns or Yields section of the documentation by merging the
    provided returns expression. If the section does not exist and the returns
    expression is provided, a new section will be created. If the section exists
    but does not have a type, it will be updated with the type from the returns
    expression.

    Args:
        sections (list[Section]): The list of documentation sections.
        returns (ast.expr | None): The returns expression to merge.
        module (str | None): The module of the object to render.

    Returns:
        None

    """
    if not (section := find_item_by_name(sections, ("Returns", "Yields"))):
        return

    if len(section.items) != 1:
        return

    item = section.items[0]

    if item.type or not returns:
        return

    if section.name == "Returns":
        item.type = returns

    elif isinstance(returns, ast.Subscript):
        ident = next(astdoc.ast.iter_identifiers(returns))
        ident = get_fullname_from_module(ident, module)
        iters = ["collections.abc.Generator", "collections.abc.Iterator"]

        if ident in iters and isinstance(returns, ast.Subscript):
            if isinstance(returns.slice, ast.Tuple):
                item.type = returns.slice.elts[0]

            else:
                item.type = returns.slice


def merge_attributes(  # noqa: C901
    sections: list[Section],
    attrs: list[Type],
    ignore_names: list[str] | None = None,
    *,
    ignore_empty: bool = True,
) -> None:
    """Merge the attributes from the given sections and attributes list.

    Update the Attributes section of the documentation by merging the provided
    attributes list. If the section does not exist and the attributes list is
    provided, a new section will be created. If the section exists but does not
    have a type, it will be updated with the type from the attributes list.

    Args:
        sections (list[Section]): The list of documentation sections.
        attrs (list[Type]): The list of attributes to merge.
        ignore_names (list[str] | None, optional): The list of attribute names
            to ignore. Used for skipping built-in attributes. Defaults to None.
        ignore_empty (bool, optional): Whether to ignore attributes with
            empty documentation. Defaults to True.

    Returns:
        None

    """
    if section := find_item_by_name(sections, "Attributes"):
        items = section.items
        created = False

    else:
        if not attrs:
            return

        items = []
        section = Section("Attributes", "", "", items)
        created = True

    for item in items:
        if item.type:
            continue

        attr = find_item_by_name(attrs, item.name)
        if attr and (attr.type or attr.doc.type):
            item.type = attr.type or attr.doc.type

    for attr in attrs:
        if ignore_names and attr.name in ignore_names:
            continue

        if attr.name.startswith("_"):
            continue

        if find_item_by_name(items, attr.name):
            continue

        type_ = attr.type or attr.doc.type
        if attr.doc.text or not ignore_empty:
            text = attr.doc.text.split("\n\n")[0]  # summary line
            item = Item(attr.name, type_, text)
            items.append(item)

    if items and created:
        sections.append(section)


def merge_sections(
    sections: list[Section],
    obj: Attribute | Class | Function | Module | Property,
) -> None:
    """Merge sections of documentation for a given object.

    Take a list of sections and an object, and merge the
    documentation sections for the object. Handle different types of
    objects, including modules, classes, functions, and properties, and
    merge attributes, parameters, raises, and returns sections as
    appropriate.

    Args:
        sections (list[Section]): The list of sections to merge.
        obj (Attribute | Class | Function | Module | Property): The object
            whose documentation sections are to be merged.

    Returns:
        None

    """
    if isinstance(obj, Module | Class):
        if isinstance(obj, Class) and is_enum(obj.name, obj.module):
            ignore_names = ["name", "value"]
            ignore_empty = False
        else:
            ignore_names = None
            ignore_empty = True

        attrs = [x for _, x in obj.get_children(Type)]
        merge_attributes(sections, attrs, ignore_names, ignore_empty=ignore_empty)

    if isinstance(obj, Function | Class):
        merge_parameters(sections, obj.parameters)
        merge_raises(sections, obj.raises)

    if isinstance(obj, Function | Property):
        merge_returns(sections, obj.node.returns, obj.module)


def create_summary_item(name: str, module: str | None) -> Item | None:
    """Create a summary item for the given name in the given module.

    Take a fully qualified name, create a parser for it,
    and extract the name set and summary from the parser.
    Construct an Item with the name, type (None), and summary.

    Args:
        name (str): The fully qualified name of the object.
        module (str): The name of the module.

    Returns:
        Item | None: The summary item if created, otherwise None.

    """
    if not (parser := Parser.create(name, module)):
        return None

    name_set = parser.parse_name_set()
    summary = parser.parse_summary()
    name = f"[{name_set.name}][{PREFIX}{name_set.id}]"
    return Item(name, None, summary)


def create_classes_from_module(module: str) -> Section | None:
    """Create a Classes section from the given module.

    Take a module name, check if it is a package,
    and iterate over the classes in the module. For each class,
    create a summary item and add it to the Classes section.

    Args:
        module (str): The name of the module.

    Returns:
        Section | None: The Classes section if created, otherwise None.

    """
    items = []
    for name in iter_classes_from_module(module):
        if item := create_summary_item(name, module):
            items.append(item)

    return Section("Classes", None, "", items) if items else None


def create_functions_from_module(module: str) -> Section | None:
    """Create a Functions section from the given module.

    Take a module name, and iterate over the functions in the module.
    For each function, create a summary item and add it to the Functions section.

    Args:
        module (str): The name of the module.

    Returns:
        Section | None: The Functions section if created, otherwise None.

    """
    items = []
    for name in iter_functions_from_module(module):
        if item := create_summary_item(name, module):
            items.append(item)

    return Section("Functions", None, "", items) if items else None


def create_modules_from_module(module: str) -> Section | None:
    """Create a Modules section from the given module.

    Take a module name, check if it is a package,
    and iterate over the submodules in the module. For each submodule,
    create a summary item and add it to the Modules section.

    Args:
        module (str): The name of the module.

    Returns:
        Section | None: The Modules section if created, otherwise None.

    """
    items = []
    for name in iter_modules_from_module(module):
        if item := create_summary_item(name, module):
            items.append(item)

    return Section("Modules", None, "", items) if items else None


def create_modules_from_module_file(module: str) -> Section | None:
    """Create a Modules section from the given module.

    Take a module name, check if it is a package,
    and iterate over the submodules in the module. For each submodule,
    create a summary item and add it to the Modules section.

    Args:
        module (str): The name of the module.

    Returns:
        Section | None: The Modules section if created, otherwise None.

    """
    if not is_package(module):
        return None

    items = []
    for name in find_submodule_names(module):
        if name.split(".")[-1].startswith("_"):
            continue

        if item := create_summary_item(name, None):
            items.append(item)

    return Section("Modules", None, "", items) if items else None


def create_methods_from_class(name: str, module: str) -> Section | None:
    """Create a Methods section from the given class.

    Take a class name and module name, and iterate over the methods in the class.
    For each method, create a summary item and add it to the Methods section.

    Args:
        name (str): The name of the class.
        module (str): The name of the module.

    Returns:
        Section | None: The Methods section if created, otherwise None.

    """
    items = []
    for method in iter_methods_from_class(name, module):
        if item := create_summary_item(f"{name}.{method}", module):
            items.append(item)

    return Section("Methods", None, "", items) if items else None
