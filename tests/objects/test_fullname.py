import ast

from mkapi.objects import _get_module_from_node

source = """
class A:
    def f(self):
        pass
    class C:
        def g(self):
            pass
"""


def test_parent():
    node = ast.parse(source)
    module = _get_module_from_node(node)
    module.name = "m"
    a = module.get_class("A")
    assert a
    f = a.get_function("f")
    assert f
    c = a.get_class("C")
    assert c
    g = c.get_function("g")
    assert g
    assert g.parent is c
    assert c.parent is a
    assert f.parent is a


def test_get_fullname(google):
    c = google.get_class("ExampleClass")
    f = c.get_function("example_method")
    assert c.get_fullname() == "examples.styles.example_google.ExampleClass"
    name = "examples.styles.example_google.ExampleClass.example_method"
    assert f.get_fullname() == name
    assert c.get_fullname("#") == "examples.styles.example_google#ExampleClass"
