from mkapi.nodes import get_node
from mkapi.objects import load_module, objects


def f():
    pass


class A:
    x: int


def test_node():
    print(A.__name__, A.__module__)
    A.x = 1
    print(A.x.__name__, A.x.__module__)
    assert 0
    # node = load_module("examples.styles.example_google")
    # print(objects)
    # node = get_node("examples.styles.example_google")
    # for m in node.walk():
    #     print(m)
    # print(node.object.text)
    # assert 0


# def test_property():
#     module = load_module("mkapi.objects")
#     assert module
#     assert module.id == "mkapi.objects"
#     f = module.get_function("get_object")
#     assert f
#     assert f.id == "mkapi.objects.get_object"
