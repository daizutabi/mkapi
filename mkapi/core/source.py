import ast
import inspect
from typing import List

import _ast
from mkapi.core.module import Module, get_module
from mkapi.core.object import get_object


def get_source(module: Module, filters: List[str] = None) -> str:
    """Returns a source for module."""
    with open(module.sourcefile, "r") as f:
        source = f.read().strip()
    if not source:
        return ""
    # return f"[DOCS](../{module.object.id}.md#{module.object.id})\n\n~~~python\n{source}\n~~~\n"
    return source


# module = get_module("mkapi.core.base")
#
# source = get_source(module)
#
# module.object.id
# module.objects
#
# obj = get_object(module.objects[0])
# inspect.getsourcelines(obj)
#
# node = ast.parse(source)
# for x in ast.iter_child_nodes(node):
#     if isinstance(x, _ast.ClassDef):
#         break
#
# x.lineno
# ast.get_source_segment(source, x)
# x.end_lineno
# dir(x)
# for a in ast.walk(x):
#     print(a)
