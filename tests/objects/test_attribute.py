import ast
import inspect

from mkapi.objects import (
    Attribute,
    Class,
    Function,
    _add_doc_comment,
    _create_module,
    create_class,
    create_module,
    iter_init_attributes,
    walk,
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
        attr0: int  #: attr0
        #: attr1
        attr1: list[str]
        attr2 = 1  #: xxx
        """attr2"""
        def __init__(self):
            self.attr3 = [1]  #: attr3
            self.attr4: str
            """attr4"""
            self.attr5: float
    '''
    source = inspect.cleandoc(src)
    node = ast.parse(source)
    module = _create_module("a", node, source)
    assert len(list(walk(module))) == 11
    it = [child for child in walk(module) if isinstance(child, Attribute)]
    assert len(it) == 8
    _add_doc_comment(it, module.source)
    for a in it:
        if a.name == "attr5":
            assert not a.doc
        else:
            assert a.doc == a.name


def test_create_attribute_module():
    module = create_module("examples.styles.google")
    assert module
    a = module.get("module_level_variable1")
    assert isinstance(a, Attribute)
    assert not a.doc
    a = module.get("module_level_variable2")
    assert isinstance(a, Attribute)
    assert a.doc


def test_iter_init_attributes(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "", None)
    assert isinstance(cls, Class)
    x = list(iter_init_attributes(cls))
    for k, (name, attr) in enumerate(x, 1):
        assert name == f"attr{k}"
        assert attr.name == f"attr{k}"
        assert attr.qualname == f"ExampleClass.attr{k}"
