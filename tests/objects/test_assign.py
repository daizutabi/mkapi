import ast
import inspect

from mkapi.objects import Assign, Class, Function, _add_doc_comment, _create_module, create_class, create_module, walk


def test_merge_attributes_comment():
    src = '''
    """Module.

    Attributes:
        a
        b
    """
    a: float  #: a
    c: int  #: c
    class A:
        attr0: int  #: attr0
        #: attr1
        attr1: list[str]
        attr2 = 1  #: xxx
        """attr2"""
        def __init__(self):
            self.attr3 = [1]  #: self.attr3
            self.attr4: str
            """self.attr4"""
            self.attr5: float
    '''
    source = inspect.cleandoc(src)
    node = ast.parse(source)
    module = _create_module("a", node, source)
    assert len(list(walk(module))) == 11
    it = [child for child in walk(module) if isinstance(child, Assign)]
    assert len(it) == 8
    _add_doc_comment(it, module.source)
    for a in it:
        if a.name == "self.attr5":
            assert not a.doc
        else:
            assert a.doc == a.name


def test_create_assign_module():
    module = create_module("examples.styles.google")
    assert module
    a = module.get("module_level_variable1")
    assert isinstance(a, Assign)
    assert not a.doc
    a = module.get("module_level_variable2")
    assert isinstance(a, Assign)
    assert a.doc


def test_create_assign_class(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert isinstance(cls, Class)
    func = cls.get("__init__")
    assert isinstance(func, Function)
    a = func.get("self.attr1")
    assert isinstance(a, Assign)


# def test_create_attribute_without_module(google):
#     module = _create_empty_module()
#     assigns = list(iter_assigns(google))
#     assert len(assigns) == 2
#     assign = get_by_name(assigns, "module_level_variable1")
#     assert assign
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "module_level_variable1"
#     assert not attr.type.expr
#     assert not attr.doc.text.str
#     assign = get_by_name(assigns, "module_level_variable2")
#     assert assign
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "module_level_variable2"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'int'"
#     assert attr.doc.text.str.startswith("Module level")
#     assert attr.doc.text.str.endswith("a colon.")


# def test_create_property_without_module(get):
#     node = get("ExampleClass")
#     assert node
#     assigns = list(iter_assigns(node))
#     assign = get_by_name(assigns, "readonly_property")
#     assert assign

#     module = _create_empty_module()
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "readonly_property"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'str'"
#     assert attr.doc.text.str.startswith("Properties should")
#     assert attr.doc.text.str.endswith("getter method.")
#     assign = get_by_name(assigns, "readwrite_property")
#     assert assign

#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "readwrite_property"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'list(str)'"
#     assert attr.doc.text.str.startswith("Properties with")
#     assert attr.doc.text.str.endswith("here.")


# def test_create_attribute_pep526_without_module(get):
#     node = get("ExamplePEP526Class")
#     assert node
#     assigns = list(iter_assigns(node))
#     assign = get_by_name(assigns, "attr1")
#     assert assign

#     module = _create_empty_module()
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "attr1"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "str"
#     assert not attr.doc.text.str
#     assign = get_by_name(assigns, "attr2")
#     assert assign

#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "attr2"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "int"
#     assert not attr.doc.text.str


# def test_class_attribute(google, source, get):
#     module = _create_module("google", google, source)
#     node = get("ExampleClass")
#     assert node
#     cls = create_class(node, module, None)
#     assert not get_by_type(cls.doc.sections, Assigns)
#     attrs = cls.attributes
#     assert len(attrs) == 7
#     names = ["attr1", "attr2", "attr3", "attr4", "attr5", "readonly_property", "readwrite_property"]
#     section = get_by_type(cls.doc.sections, Attributes)
#     assert section
#     for x in [section.items, cls.attributes]:
#         for k, name in enumerate(names):
#             assert x[k].name.str == name
#     assert not get_by_name(cls.functions, "__init__")


# def test_create_module_attribute_with_module(google, source):
#     module = _create_module("google", google, source)
#     attrs = module.attributes
#     assert len(attrs) == 2
#     attr = attrs[0]
#     assert attr.name.str == "module_level_variable1"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'int'"
#     assert attr.doc.text.str
#     assert attr.doc.text.str.startswith("Module level")
#     assert attr.doc.text.str.endswith("with it.")
#     assert not get_by_type(module.doc.sections, Assigns)
