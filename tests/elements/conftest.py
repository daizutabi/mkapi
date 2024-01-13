import ast
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.utils import get_module_path


@pytest.fixture(scope="module")
def module():
    path = get_module_path("mkdocs.structure.files")
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


def load_module(name):
    path = str(Path(__file__).parent.parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
    path = get_module_path(name)
    assert path
    with path.open("r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source)


@pytest.fixture(scope="module")
def google():
    return load_module("examples.styles.example_google")


@pytest.fixture(scope="module")
def get(google):
    def get(name, *rest, node=google):
        for child in iter_child_nodes(node):
            if not isinstance(child, ast.FunctionDef | ast.ClassDef):
                continue
            if child.name == name:
                if not rest:
                    return child
                return get(*rest, node=child)
        raise NameError

    return get
