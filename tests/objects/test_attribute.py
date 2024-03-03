import ast
import inspect


def test_merge_attributes_comment():
    from mkapi.objects import Attribute, create_module, iter_objects

    src = '''
    """Module.

    Attributes:
        a
        b
    """
    a: float  #: a
    c: int  #: c
    class A:
        attr0: int  #: int: attr0
        #: attr1
        attr1: list[str]
        attr2 = 1  #: xxx
        """attr2"""
        def __init__(self):
            self.attr3 = [1]  #: list: attr3
            self.attr4: str  #: yyy
            """attr4"""
            self.attr5: float
    '''
    source = inspect.cleandoc(src)
    node = ast.parse(source)
    module = create_module("test_merge_attributes_comment", node, source)
    assert module
    for a in iter_objects(module, Attribute):
        if a.name == "attr5":
            assert not a.doc.text
        else:
            assert a.doc.text == a.name


def test_create_attribute_module():
    from mkapi.objects import Attribute, create_module

    module = create_module("examples.styles.google")
    assert module
    a = module.get("module_level_variable1")
    assert isinstance(a, Attribute)
    assert not a.doc.text
    a = module.get("module_level_variable2")
    assert isinstance(a, Attribute)
    assert a.doc.text


def test_iter_init_attributes(get):
    from mkapi.objects import Class, Function, create_class, iter_attributes_from_function

    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "test_iter_init_attributes", None)
    assert isinstance(cls, Class)
    func = cls.get("__init__")
    assert isinstance(func, Function)
    x = list(iter_attributes_from_function(func, cls))
    for k, attr in enumerate(x, 1):
        assert attr.name == f"attr{k}"
        assert attr.qualname == f"ExampleClass.attr{k}"


def test_attribute_doc():
    from mkapi.objects import Class, create_module

    module = create_module("examples.styles.google")
    assert module
    attr = module.get("module_level_variable2")
    assert attr
    assert attr.doc.type == "int"
    assert attr.doc.text.startswith("Module")
    assert attr.doc.text.endswith("a colon.")
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    attr = cls.get("attr3")
    assert attr
    assert attr.doc.text == "Doc comment *inline* with attribute"
    attr = cls.get("attr4")
    assert attr
    assert attr.doc.type == "list(str)"
    attr = cls.get("attr5")
    assert attr
    assert attr.doc.type == "str"
    attr = cls.get("readonly_property")
    assert attr
    assert attr.doc.type == "str"
    attr = cls.get("readwrite_property")
    assert attr
    assert attr.doc.type == "list(str)"
    assert attr.doc.text.startswith("Properties")
    assert attr.doc.text.endswith("here.")
