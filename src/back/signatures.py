from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mkapi.ast import PARAMETER_KIND_ATTRIBUTE
from mkapi.objects import Attribute, Class, Function

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.items import Parameter


@dataclass
class Part:
    """Signature part."""

    markdown: str
    kind: str


@dataclass
class Signature:
    """Signature."""

    parts: list[Part]

    def __iter__(self) -> Iterator[Part]:
        return iter(self.parts)


def _iter_sep(kind: str | None, prev_kind: str | None) -> Iterator[tuple[str, str]]:
    if prev_kind == "posonlyargs" and kind != prev_kind:
        yield "/", "slash"
        yield ", ", "comma"

    if kind == "kwonlyargs" and prev_kind not in [kind, "vararg"]:
        yield r"\*", "star"
        yield ", ", "comma"

    if kind == "vararg":
        yield r"\*", "star"

    if kind == "kwarg":
        yield r"\*\*", "star"


def _iter_param(param: Parameter) -> Iterator[tuple[str, str]]:
    if param.type.expr:
        yield ": ", "colon"
        yield param.type.markdown, "ann"

    if param.default.expr:
        eq = " = " if param.type.expr else "="
        yield eq, "equal"
        yield param.default.markdown, "default"


def iter_signature(obj: Class | Function) -> Iterator[tuple[str, str]]:
    """Yield signature."""
    yield "(", "paren"
    n = len(obj.parameters)
    prev_kind = kind = None

    for k, param in enumerate(obj.parameters):
        if k == 0 and obj.kind in ["class", "method", "classmethod"]:
            continue

        kind = PARAMETER_KIND_ATTRIBUTE[param.kind]
        yield from _iter_sep(kind, prev_kind)

        yield param.name.str.replace("_", "\\_"), "arg"
        yield from _iter_param(param)

        if k < n - 1:
            yield ", ", "comma"

        prev_kind = kind

    if kind == "posonlyargs":
        yield ", ", "comma"
        yield "/", "slash"

    yield ")", "paren"

    if isinstance(obj, Class) or not obj.returns:
        return

    yield " → ", "arrow"
    yield obj.returns[0].type.markdown, "return"


def get_signature(obj: Class | Function | Attribute) -> Signature:
    """Return signature."""
    if isinstance(obj, Class | Function):
        parts = [Part(*args) for args in iter_signature(obj)]
        return Signature(parts)

    return Signature([Part(": ", "colon"), Part(obj.type.markdown, "return")])
