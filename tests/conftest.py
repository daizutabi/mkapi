import importlib
import inspect
import os
import sys

import pytest

from mkapi.core.parser import Parser

sys.path.insert(0, os.path.abspath("tests"))


@pytest.fixture(scope="session")
def example():
    import example_google as example

    yield example


import ast

with open(r'tests\example_google.py') as f:
    source = f.read()


node = ast.parse(source)
ast.get_docstring(node.body[-2])
dir(node.body[-1].body[1].body[2])

dir(node.body[-1].body[1].body[2].targets[0])
node.body[-1].body[1].body[2].targets[0].attr
node.body[-1].body[1].body[2].targets[0].value.id
node.body[-1].body[1].body[1].lineno
node.body[-1].body[1].end_lineno
