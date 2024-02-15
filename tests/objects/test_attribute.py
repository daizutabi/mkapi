import ast

from mkapi.items import iter_assigns
from mkapi.objects import create_attribute
from mkapi.utils import get_by_name


def test_create_attribute_without_module(google):
    assigns = list(iter_assigns(google))
    assert len(assigns) == 2
    assign = get_by_name(assigns, "module_level_variable1")
    assert assign
    attr = create_attribute(assign)
    assert attr.name.str == "module_level_variable1"
    assert not attr.type.expr
    assert not attr.doc.text.str
    assign = get_by_name(assigns, "module_level_variable2")
    assert assign
    attr = create_attribute(assign)
    assert attr.name.str == "module_level_variable2"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "int"
    assert attr.doc.text.str.startswith("Module level")
    assert attr.doc.text.str.endswith("a colon.")


def test_create_property_without_module(get):
    node = get("ExampleClass")
    assert node
    assigns = list(iter_assigns(node))
    assign = get_by_name(assigns, "readonly_property")
    assert assign
    attr = create_attribute(assign)
    assert attr.name.str == "readonly_property"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "str"
    assert attr.doc.text.str.startswith("Properties should")
    assert attr.doc.text.str.endswith("getter method.")
    assign = get_by_name(assigns, "readwrite_property")
    assert assign
    attr = create_attribute(assign)
    assert attr.name.str == "readwrite_property"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "list[str]"
    assert attr.doc.text.str.startswith("Properties with")
    assert attr.doc.text.str.endswith("here.")


def test_create_attribute_pep526_without_module(get):
    node = get("ExamplePEP526Class")
    assert node
    assigns = list(iter_assigns(node))
    assign = get_by_name(assigns, "attr1")
    assert assign
    attr = create_attribute(assign)
    assert attr.name.str == "attr1"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "str"
    assert not attr.doc.text.str
    assign = get_by_name(assigns, "attr2")
    assert assign
    attr = create_attribute(assign)
    assert attr.name.str == "attr2"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "int"
    assert not attr.doc.text.str


# def test_attribute_comment():
#     src = '''
#     """Module.

#     Attributes:
#         a
#         b
#     """
#     a: float  #: Doc comment *inline* with attribute.
#     c: int  #: C
#     class A:
#         attr0: int  #: Doc comment *inline* with attribute.
#         #: list(str): Doc comment *before* attribute, with type specified.
#         attr1: list[str]
#         attr2 = 1
#         attr3 = [1]  #: list(int): Doc comment *inline* with attribute.
#         attr4: str
#         """Docstring *after* attribute, with type specified."""
#         attr5: float
#     '''
#     src = inspect.cleandoc(src)
#     node = ast.parse(src)
#     module = create_module("a", node, src)
#     t = module.attributes[0].doc.text.str
#     assert t == "Doc comment *inline* with attribute."
#     a = module.classes[0].attributes
#     assert a[0].doc.text.str == "Doc comment *inline* with attribute."
#     assert a[1].doc.text.str
#     assert a[1].doc.text.str.startswith("Doc comment *before* attribute, with")
#     assert isinstance(a[1].type.expr, ast.Subscript)
#     assert a[2].doc.text.str is None
#     assert a[3].doc.text.str == "Doc comment *inline* with attribute."
#     assert isinstance(a[3].type.expr, ast.Subscript)
#     assert a[4].doc.text.str == "Docstring *after* attribute, with type specified."
#     assert a[5].doc.text.str is None
