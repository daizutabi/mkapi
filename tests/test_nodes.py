from mkapi.nodes import get_node
from mkapi.objects import load_module, objects


def test_node():
    node = load_module("examples.styles.example_google")
    print(objects)
    node = get_node("examples.styles.example_google")
    for m in node.walk():
        print(m)
    print(node.object.text)
    # assert 0


# def test_property():
#     module = load_module("mkapi.objects")
#     assert module
#     assert module.id == "mkapi.objects"
#     f = module.get_function("get_object")
#     assert f
#     assert f.id == "mkapi.objects.get_object"
