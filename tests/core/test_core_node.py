from mkapi.core.node import get_node


def test_generator():
    node = get_node("google_style.gen")
    assert node.object.kind == "generator"


def test_class():
    node = get_node("google_style.ExampleClass")
    assert node.object.prefix == "google_style"
    assert node.object.name == "ExampleClass"
    assert node.object.kind == "class"
    assert len(node) == 3
    p = node.members[-1]
    assert p.object.type.name == "list of int"
    assert p.docstring.sections[0].markdown.startswith("Read-write property")


def test_dataclass():
    node = get_node("google_style.ExampleDataClass")
    assert node.object.prefix == "google_style"
    assert node.object.name == "ExampleDataClass"
    assert node.object.kind == "dataclass"
