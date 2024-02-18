import ast
import inspect

from mkapi.items import Assigns, iter_assigns
from mkapi.objects import (
    Attributes,
    _create_empty_module,
    _create_module,
    _merge_attributes_comment,
    create_attribute,
    create_class,
    iter_attributes,
)
from mkapi.utils import get_by_name, get_by_type


def test_merge_attributes_comment():
    src = '''
    """Module.

    Attributes:
        a
        b
    """
    a: float  #: Doc comment *inline* with attribute.
    c: int  #: C
    class A:
        attr0: int  #: Doc comment *inline* with attribute.
        #: list(str): Doc comment *before* attribute, with type specified.
        attr1: list[str]
        attr2 = 1
        attr3 = [1]  #: list(int): Doc comment *inline* with attribute.
        attr4: str
        """Docstring *after* attribute, with type specified."""
        attr5: float
    '''
    source = inspect.cleandoc(src)
    node = ast.parse(source)
    module = _create_module("a", node, source)
    attrs = list(iter_attributes(node, module, None))
    _merge_attributes_comment(attrs, source)
    assert len(attrs) == 2
    attr = get_by_name(attrs, "a")
    assert attr
    assert attr.doc.text.str == "Doc comment *inline* with attribute."
    attr = get_by_name(attrs, "c")
    assert attr
    assert attr.doc.text.str == "C"

    for cls in ast.iter_child_nodes(node):
        if isinstance(cls, ast.ClassDef):
            break

    assert isinstance(cls, ast.ClassDef)
    a = list(iter_attributes(cls, module, None))
    _merge_attributes_comment(a, source)
    assert len(a) == 6
    assert a[0].doc.text.str == "Doc comment *inline* with attribute."
    assert a[1].doc.text.str
    assert a[1].doc.text.str.startswith("Doc comment *before* attribute, with")
    assert a[1].type.expr
    assert ast.unparse(a[1].type.expr) == "list[str]"
    assert not a[2].doc.text.str
    assert a[3].doc.text.str == "Doc comment *inline* with attribute."
    assert a[3].type.expr
    assert ast.unparse(a[3].type.expr) == "'list(int)'"
    assert a[4].doc.text.str == "Docstring *after* attribute, with type specified."
    assert not a[5].doc.text.str


def test_create_attribute_without_module(google):
    module = _create_empty_module()
    assigns = list(iter_assigns(google))
    assert len(assigns) == 2
    assign = get_by_name(assigns, "module_level_variable1")
    assert assign
    attr = create_attribute(assign, module, None)
    assert attr.name.str == "module_level_variable1"
    assert not attr.type.expr
    assert not attr.doc.text.str
    assign = get_by_name(assigns, "module_level_variable2")
    assert assign
    attr = create_attribute(assign, module, None)
    assert attr.name.str == "module_level_variable2"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "'int'"
    assert attr.doc.text.str.startswith("Module level")
    assert attr.doc.text.str.endswith("a colon.")


def test_create_property_without_module(get):
    node = get("ExampleClass")
    assert node
    assigns = list(iter_assigns(node))
    assign = get_by_name(assigns, "readonly_property")
    assert assign

    module = _create_empty_module()
    attr = create_attribute(assign, module, None)
    assert attr.name.str == "readonly_property"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "'str'"
    assert attr.doc.text.str.startswith("Properties should")
    assert attr.doc.text.str.endswith("getter method.")
    assign = get_by_name(assigns, "readwrite_property")
    assert assign

    attr = create_attribute(assign, module, None)
    assert attr.name.str == "readwrite_property"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "'list(str)'"
    assert attr.doc.text.str.startswith("Properties with")
    assert attr.doc.text.str.endswith("here.")


def test_create_attribute_pep526_without_module(get):
    node = get("ExamplePEP526Class")
    assert node
    assigns = list(iter_assigns(node))
    assign = get_by_name(assigns, "attr1")
    assert assign

    module = _create_empty_module()
    attr = create_attribute(assign, module, None)
    assert attr.name.str == "attr1"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "str"
    assert not attr.doc.text.str
    assign = get_by_name(assigns, "attr2")
    assert assign

    attr = create_attribute(assign, module, None)
    assert attr.name.str == "attr2"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "int"
    assert not attr.doc.text.str


def test_class_attribute(google, source, get):
    module = _create_module("google", google, source)
    node = get("ExampleClass")
    assert node
    cls = create_class(node, module, None)
    assert not get_by_type(cls.doc.sections, Assigns)
    attrs = cls.attributes
    assert len(attrs) == 7
    names = ["attr1", "attr2", "attr3", "attr4", "attr5", "readonly_property", "readwrite_property"]
    section = get_by_type(cls.doc.sections, Attributes)
    assert section
    for x in [section.items, cls.attributes]:
        for k, name in enumerate(names):
            assert x[k].name.str == name
    assert not get_by_name(cls.functions, "__init__")


def test_create_module_attribute_with_module(google, source):
    module = _create_module("google", google, source)
    attrs = module.attributes
    assert len(attrs) == 2
    attr = attrs[0]
    assert attr.name.str == "module_level_variable1"
    assert attr.type.expr
    assert ast.unparse(attr.type.expr) == "'int'"
    assert attr.doc.text.str
    assert attr.doc.text.str.startswith("Module level")
    assert attr.doc.text.str.endswith("with it.")
    assert not get_by_type(module.doc.sections, Assigns)
