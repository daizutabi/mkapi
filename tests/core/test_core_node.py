from mkapi.core.node import get_node


def test_generator():
    node = get_node("example.gen")
    assert node.kind == "generator"


def test_class():
    node = get_node("example.ExampleClass")
    assert node.name == "example.ExampleClass"
    assert node.kind == "class"
    assert node.depth == 0
    assert node.message is node[0]
    assert node.message.type == "list of str"
    assert len(node) == 3
    for x in node:
        pass
    assert x.type == 'list of int'
    assert x.markdown.startswith('Read-write property')


def test_dataclass():
    node = get_node("example.ExampleDataClass")
    assert node.name == "example.ExampleDataClass"
    assert node.kind == "dataclass"
    assert node.depth == 0
