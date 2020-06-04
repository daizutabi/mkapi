from mkapi.core.node import get_node


def test_generator():
    node = get_node("google_style.gen")
    assert node.kind == "generator"


def test_class():
    node = get_node("google_style.ExampleClass")
    assert node.prefix == "google_style"
    assert node.name == "ExampleClass"
    assert node.kind == "class"
    assert node.depth == 0
    assert len(node) == 3
    p = node.members[-1]
    assert p.type == "list of int"
    assert p.docstring.sections[0].markdown.startswith("Read-write property")


def test_dataclass():
    node = get_node("google_style.ExampleDataClass")
    assert node.prefix == "google_style"
    assert node.name == "ExampleDataClass"
    assert node.kind == "dataclass"
    assert node.depth == 0
