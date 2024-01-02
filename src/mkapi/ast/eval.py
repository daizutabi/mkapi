"""Parse expr node."""
from __future__ import annotations

import ast
import re

# NAME_PATTERN = re.compile("__mkapi_()__[]")
from collections.abc import Iterator


class Transformer(ast.NodeTransformer):  # noqa: D101
    def _rename(self, name: str) -> ast.Name:
        return ast.Name(id=f"__mkapi__.{name}")

    def visit_Name(self, node: ast.Name) -> ast.Name:  # noqa: N802, D102
        return self._rename(node.id)

    def unparse(self, node: ast.expr | ast.type_param) -> str:  # noqa: D102
        return ast.unparse(self.visit(node))


class StringTransformer(Transformer):  # noqa: D101
    def visit_Constant(self, node: ast.Constant) -> ast.Constant | ast.Name:  # noqa: N802, D102
        if isinstance(node.value, str):
            return self._rename(node.value)
        return node


def iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers as a tuple of (code, is_identifier)."""
    start = 0
    while start < len(source):
        index = source.find("__mkapi__.", start)
        if index == -1:
            yield source[start:], False
            return
        else:
            if index != 0:
                yield source[start:index], False
            start = end = index + 10  # 10 == len("__mkapi__.")
            while end < len(source):
                s = source[end]
                if s == "." or s.isdigit() or s.isidentifier():
                    end += 1
                else:
                    break
            yield source[start:end], True
            start = end
