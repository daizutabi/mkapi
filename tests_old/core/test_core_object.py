from mkapi.core.node import Node
from mkapi.core.object import (
    get_object,
    get_origin,
    get_qualname,
    get_sourcefile_and_lineno,
    split_prefix_and_name,
)


def test_get_object():
    obj = get_object("mkapi.core.node.Node")
    assert obj is Node


def test_get_origin():
    obj = get_object("mkapi.core.node.Node")
    org = get_origin(obj)
    assert org is Node


def test_get_module_sourcefile_and_lineno():
    sourcefile, _ = get_sourcefile_and_lineno(Node)
    assert sourcefile.endswith("node.py")


def test_split_prefix_and_name():
    prefix, name = split_prefix_and_name(Node)
    assert prefix == "mkapi.core.node"
    assert name == "Node"


def test_qualname():
    assert get_qualname(Node) == "Node"
