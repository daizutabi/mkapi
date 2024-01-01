import ast

import pytest

from mkapi.modules import get_module


def test_():
    module = get_module("mkdocs.commands.build")
    names = module.get_names()
    node = module.get_node("get_context")
    print(ast.unparse(node))
    # assert 0
