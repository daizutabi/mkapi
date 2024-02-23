"""Link module."""
from __future__ import annotations

import ast
import re
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Literal, TypeAlias

import mkapi.ast
import mkapi.markdown
from mkapi.nodes import resolve
from mkapi.objects import Attribute, Class, Function, Module
from mkapi.utils import is_identifier, iter_identifiers, iter_parent_module_names

PREFIX = "__mkapi__."

LINK_PATTERN = re.compile(r"(?<!\])\[(?P<name>[^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


def get_markdown_link(name: str, ref: str | None) -> str:
    name = name.replace("_", "\\_")
    return f"[{name}][{PREFIX}{ref}]" if ref else name


Replace: TypeAlias = Callable[[str], str | None] | None


def get_markdown_name(fullname: str, replace: Replace = None) -> str:
    """Return markdown links"""
    names = fullname.split(".")
    refs = iter_parent_module_names(fullname)

    if replace:
        refs = [replace(ref) for ref in refs]

    it = zip(names, refs, strict=True)
    return ".".join(get_markdown_link(*names) for names in it)


def get_markdown_str(type_string: str, replace: Replace) -> str:
    """Return markdown links from string-type."""
    it = iter_identifiers(type_string)
    markdowns = (get_markdown_name(name, replace) if is_ else name for name, is_ in it)
    return "".join(markdowns)


def get_markdown_expr(expr: ast.expr, replace: Replace = None) -> str:
    """Set Markdown text with link."""
    if isinstance(expr, ast.Constant):
        value = expr.value

        if isinstance(value, str):
            return get_markdown_str(value, replace)

        return str(value)

    def get_link(name: str) -> str:
        return get_markdown_name(name, replace)

    try:
        return mkapi.ast.unparse(expr, get_link)
    except ValueError:
        return ast.unparse(expr)


def get_markdown_text(text: str, replace: Replace) -> str:
    """Return markdown links from docstring text."""

    def _replace(match: re.Match) -> str:
        name = match.group("name")

        if name.startswith("__mkapi__."):
            from_mkapi = True
            name = name[10:]
        else:
            from_mkapi = False

        if is_identifier(name) and replace and (ref := replace(name)):
            return get_markdown_link(name, ref)

        if from_mkapi:
            return name

        return match.group()

    return mkapi.markdown.sub(LINK_PATTERN, _replace, text)


# def _merge_attributes(
#     attributes: list[Attribute],
#     module: Module,
#     parent_doc: Module | Class | Function | None,
#     parent_create: Class | Function | None,
# ) -> None:
#     """Merge attributes."""
#     sections = parent_doc.doc.sections if parent_doc else module.doc.sections

#     if section := get_by_type(sections, Assigns):
#         for attr in attributes:
#             _merge_attribute_docstring(attr, section)

#         for item in reversed(section.items):
#             attr = create_attribute(item, module, parent_create)
#             attributes.insert(0, attr)

#     if module.source:
#         _merge_attributes_comment(attributes, module.source)


# def _merge_attribute_docstring(attr: Attribute, section: Assigns):
#     if item := get_by_name(section.items, attr.name):
#         if not attr.doc.text.str:
#             attr.doc.text.str = item.text.str

#         if not attr.type.expr:
#             attr.type.expr = item.type.expr

#         index = section.items.index(item)
#         del section.items[index]


# def _add_attributes_section(doc: Docstring, attrs: list[Attribute]):
#     """Add an Attributes section."""
#     items = []

#     for attr in attrs:
#         if attr.doc.sections:
#             item = create_summary_item(attr.name, attr.doc, attr.type)
#             items.append(item)
#         elif attr.doc.text.str:
#             item = Item(attr.name, attr.type, attr.doc.text)
#             items.append(item)

#     if not items:
#         return

#     section = Attributes(Name("Attributes"), Type(), Text(), items)

#     if section_assigns := get_by_type(doc.sections, Assigns):
#         index = doc.sections.index(section_assigns)
#         doc.sections[index] = section
#     else:
#         doc.sections.append(section)

#     return


# def _union_attributes(la: list[Attribute], lb: list[Attribute]) -> Iterator[Attribute]:
#     """Yield merged [Attribute] instances."""
#     for name in unique_names(la, lb):
#         a, b = get_by_name(la, name), get_by_name(lb, name)

#         if a and not b:
#             yield a

#         elif not a and b:
#             yield b

#         elif isinstance(a, Attribute) and isinstance(b, Attribute):
#             a.node = a.node if a.node else b.node
#             a.type = a.type if a.type.expr else b.type
#             a.doc = mkapi.docstrings.merge(a.doc, b.doc)
#             yield a


# def is_member(
#     obj: Module | Class | Function | Attribute,
#     parent: Module | Class | Function | None,
# ) -> bool:
#     """Return True if obj is a member of parent."""
#     if parent is None or isinstance(obj, Module) or isinstance(parent, Module):
#         return True

#     if obj.parent is not parent:
#         return False

#     return obj.module is parent.module


# def iter_objects_with_depth(
#     obj: Module | Class | Function | Attribute,
#     maxdepth: int = -1,
#     predicate: Predicate = None,
#     depth: int = 0,
# ) -> Iterator[tuple[Module | Class | Function | Attribute, int]]:
#     """Yield [Object] instances and depth."""
#     if not predicate or predicate(obj, None):
#         yield obj, depth

#     if depth == maxdepth or isinstance(obj, Attribute):
#         return

#     for child in itertools.chain(obj.classes, obj.functions):
#         if not predicate or predicate(child, obj):
#             yield from iter_objects_with_depth(child, maxdepth, predicate, depth + 1)

#     if isinstance(obj, Module | Class):
#         for attr in obj.attributes:
#             if not predicate or predicate(attr, obj):
#                 yield attr, depth + 1


# def iter_objects(
#     obj: Module | Class | Function | Attribute,
#     maxdepth: int = -1,
#     predicate: Predicate = None,
# ) -> Iterator[Module | Class | Function | Attribute]:
#     """Yield [Object] instances."""
#     for child, _ in iter_objects_with_depth(obj, maxdepth, predicate, 0):
#         yield child

# def is_empty(obj: Object) -> bool:
#     """Return True if a [Object] instance is empty."""
#     if isinstance(obj, Attribute) and not obj.doc.sections:
#         return True

#     if not docstrings.is_empty(obj.doc):
#         return False

#     if isinstance(obj, Function) and obj.name.str.startswith("_"):
#         return True

#     return False

# def merge_sections(a: Section, b: Section) -> Section:
#     """Merge two [Section] instances into one [Section] instance."""
#     if a.name != b.name:
#         raise ValueError
#     type_ = a.type if a.type.expr else b.type
#     text = Text(f"{a.text.str or ''}\n\n{b.text.str or ''}".strip())
#     return Section(a.name, type_, text, list(iter_merged_items(a.items, b.items)))


# def iter_merge_sections(a: list[Section], b: list[Section]) -> Iterator[Section]:
#     """Yield merged [Section] instances from two lists of [Section]."""
#     for name in unique_names(a, b):
#         if name:
#             ai, bi = get_by_name(a, name), get_by_name(b, name)
#             if ai and not bi:
#                 yield ai
#             elif not ai and bi:
#                 yield bi
#             elif ai and bi:
#                 yield merge_sections(ai, bi)


# def merge(a: Docstring, b: Docstring) -> Docstring:
#     """Merge two [Docstring] instances into one [Docstring] instance."""
#     sections: list[Section] = []
#     for ai in a.sections:
#         if ai.name:
#             break
#         sections.append(ai)
#     sections.extend(iter_merge_sections(a.sections, b.sections))
#     is_named_section = False
#     for section in a.sections:
#         if section.name:  # already collected, so skip.
#             is_named_section = True
#         elif is_named_section:
#             sections.append(section)
#     sections.extend(s for s in b.sections if not s.name)
#     type_ = a.type  # if a.type.expr else b.type
#     text = Text(f"{a.text.str or ''}\n\n{b.text.str or ''}".strip())
#     return Docstring(Name("Docstring"), type_, text, sections)


# def is_empty(doc: Docstring) -> bool:
#     """Return True if a [Docstring] instance is empty."""
#     if doc.text.str:
#         return False
#     for section in doc.sections:
#         if section.text.str:
#             return False
#         for item in section.items:
#             if item.text.str:
#                 return False
#     return True


# def create_summary_item(name: Name, doc: Docstring, type_: Type | None = None):
#     text = doc.text.str.split("\n\n")[0]  # summary line
#     return Item(name, type_ or Type(), Text(text))


# def merge_parameters(sections: list[Section], parameters: list[Parameter]) -> None:
#     """Merge parameters."""
#     if not (section := get_by_type(sections, Parameters)):
#         return

#     for item in section.items:
#         name = item.name.str.replace("*", "")

#         if param := get_by_name(parameters, name):
#             if not item.type.expr:
#                 item.type = param.type

#             if not item.default.expr:
#                 item.default = param.default

#             item.kind = param.kind


# def merge_returns(sections: list[Section], returns: list[Return]) -> None:
#     """Merge returns."""
#     if not (section := get_by_type(sections, Returns)):
#         return

#     if len(returns) == 1 and len(section.items) == 1:
#         item = section.items[0]

#         if not item.type.expr:
#             item.type = returns[0].type


# def merge_raises(sections: list[Section], raises: list[Raise]) -> None:
#     """Merge raises."""
#     section = get_by_type(sections, Raises)

#     if not section:
#         if not raises:
#             return

#         section = create_raises([])
#         sections.append(section)

#     section.items = list(iter_merged_items(section.items, raises))


# T = TypeVar("T")


# def iter_merged_items(la: Sequence[T], lb: Sequence[T]) -> Iterator[T]:
#     """Yield merged [Item] instances."""
#     for name in unique_names(la, lb):
#         a, b = get_by_name(la, name), get_by_name(lb, name)
#         if a and not b:
#             yield a
#         elif not a and b:
#             yield b
#         elif isinstance(a, Item) and isinstance(b, Item):
#             a.name = a.name if a.name.str else b.name
#             a.type = a.type if a.type.expr else b.type
#             a.text = a.text if a.text.str else b.text
#             yield a
