import ast
import inspect

from mkapi.objects import (
    Attribute,
    Class,
    Function,
    _create_module,
    create_class,
    create_module,
    iter_attributes_from_method,
)


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
    module = _create_module("a", node, source)
    for a in module.iter_objects(Attribute):
        if a.name == "attr5":
            assert not a.doc.text
        else:
            assert a.doc.text == a.name


def test_create_attribute_module():
    module = create_module("examples.styles.google")
    assert module
    a = module.get("module_level_variable1")
    assert isinstance(a, Attribute)
    assert not a.doc.text
    a = module.get("module_level_variable2")
    assert isinstance(a, Attribute)
    assert a.doc.text


def test_iter_init_attributes(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert isinstance(cls, Class)
    func = cls.get("__init__")
    assert isinstance(func, Function)
    x = list(iter_attributes_from_method(func, cls.qualname))
    for k, (name, attr) in enumerate(x, 1):
        assert name == f"attr{k}"
        assert attr.name == f"attr{k}"
        assert attr.qualname == f"ExampleClass.attr{k}"


def test_attribute_doc():
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
