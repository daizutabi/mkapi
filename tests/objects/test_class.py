import ast
import inspect

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.importlib import load_module
from mkapi.items import iter_assigns
from mkapi.objects import (
    Class,
    Function,
    Module,
    create_attribute,
    create_class,
    create_function,
    create_module,
    iter_objects,
    objects,
)
from mkapi.utils import get_by_name, get_module_node


@pytest.fixture(scope="module")
def google():
    return get_module_node("examples.styles.google")


@pytest.fixture(scope="module")
def get(google):
    def get(name, *rest, node=google):
        for child in iter_child_nodes(node):
            if not isinstance(child, ast.FunctionDef | ast.ClassDef):
                continue
            if child.name == name:
                if not rest:
                    return child
                return get(*rest, node=child)
        raise NameError

    return get


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


def test_create_function(get):
    node = get("module_level_function")
    assert isinstance(node, ast.FunctionDef)
    func = create_function(node)
    assert isinstance(func, Function)
    assert func.name.str == "module_level_function"
    assert func.qualname.str == "module_level_function"
    assert func.fullname.str == "__mkapi__.module_level_function"
    assert "__mkapi__.module_level_function" in objects
    assert objects["__mkapi__.module_level_function"] is func
    assert len(func.parameters) == 4
    assert get_by_name(func.parameters, "param1")
    assert get_by_name(func.parameters, "param2")
    assert get_by_name(func.parameters, "args")
    assert get_by_name(func.parameters, "kwargs")
    assert len(func.returns) == 0
    assert len(func.raises) == 1
    assert len(func.doc.sections) == 3
    assert repr(func) == "Function('module_level_function')"


def test_create_class(get):
    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node)
    assert isinstance(cls, Class)
    assert cls.name.str == "ExampleClass"
    assert len(cls.parameters) == 0
    assert len(cls.raises) == 0
    assert len(cls.functions) == 6
    assert get_by_name(cls.functions, "__init__")
    assert get_by_name(cls.functions, "example_method")
    assert get_by_name(cls.functions, "__special__")
    assert get_by_name(cls.functions, "__special_without_docstring__")
    assert get_by_name(cls.functions, "_private")
    assert get_by_name(cls.functions, "_private_without_docstring")
    assert len(cls.attributes) == 2
    assert get_by_name(cls.attributes, "readonly_property")
    assert get_by_name(cls.attributes, "readwrite_property")
    func = get_by_name(cls.functions, "__init__")
    assert isinstance(func, Function)
    assert func.qualname.str == "ExampleClass.__init__"
    assert func.fullname.str == "__mkapi__.ExampleClass.__init__"
    assert repr(cls) == "Class('ExampleClass')"


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


# def test_create_class_nested():
#     src = """
#     class A:
#         class B:
#             class C:
#                 pass
#     """
#     node = ast.parse(inspect.cleandoc(src)).body[0]
#     assert isinstance(node, ast.ClassDef)
#     cls = create_class(node)
#     assert len(cls.classes) == 1
#     assert len(cls.classes[0].classes) == 1


# def test_create_module(google):
#     module = create_module("google", google)
#     assert module.name.str == "google"
#     assert len(module.functions) == 4
#     assert len(module.classes) == 3
#     cls = get_by_name(module.classes, "ExampleClass")
#     assert isinstance(cls, Class)
#     assert cls.fullname.str == "google.ExampleClass"
#     func = get_by_name(cls.functions, "example_method")
#     assert isinstance(func, Function)
#     assert func.fullname.str == "google.ExampleClass.example_method"
#     assert repr(module) == "Module('google')"
#     assert len(module.attributes) == 2


# def test_fullname(google):
#     module = create_module("examples.styles.google", google)
#     c = get_by_name(module.classes, "ExampleClass")
#     assert isinstance(c, Class)
#     f = get_by_name(c.functions, "example_method")
#     assert isinstance(f, Function)
#     assert c.fullname.str == "examples.styles.google.ExampleClass"
#     name = "examples.styles.google.ExampleClass.example_method"
#     assert f.fullname.str == name


# def test_merge_items():
#     """'''test'''
#     def f(x: int = 0, y: str = 's') -> bool:
#         '''function.

#         Args:
#             x: parameter x.
#             z: parameter z.

#         Returns:
#             Return True.'''
#     """
#     src = inspect.getdoc(test_merge_items)
#     assert src
#     node = ast.parse(src)
#     module = create_module("x", node)
#     func = get_by_name(module.functions, "f")
#     assert func
#     # merge_parameters(func)
#     assert get_by_name(func.parameters, "x")
#     assert get_by_name(func.parameters, "y")
#     assert not get_by_name(func.parameters, "z")
#     items = get_by_name(func.doc.sections, "Parameters").items  # type: ignore
#     assert get_by_name(items, "x")
#     assert not get_by_name(items, "y")
#     assert get_by_name(items, "z")
#     assert [item.name.str for item in items] == ["x", "z"]
#     # merge_returns(func)
#     assert func.returns[0].type
#     assert func.returns[0].text.str == "Return True."
#     item = get_by_name(func.doc.sections, "Returns").items[0]  # type: ignore
#     assert item.type.expr.id == "bool"  # type: ignore


# def test_iter_objects():
#     """'''test module.'''
#     m: str
#     n = 1
#     '''int: attribute n.'''
#     class A(D):
#         '''class.

#         Attributes:
#             a: attribute a.
#         '''
#         a: int
#         def f(x: int, y: str) -> list[str]:
#             '''function.'''
#             class B(E,F.G):
#                 c: list
#             raise ValueError
#     """
#     src = inspect.getdoc(test_iter_objects)
#     assert src
#     node = ast.parse(src)
#     module = create_module("x", node)
#     cls = get_by_name(module.classes, "A")
#     assert cls
#     func = get_by_name(cls.functions, "f")
#     assert func
#     cls = get_by_name(func.classes, "B")
#     assert cls
#     assert cls.fullname.str == "x.A.f.B"
#     objs = iter_objects(module)
#     assert next(objs).name.str == "x"
#     assert next(objs).name.str == "A"
#     assert next(objs).name.str == "f"
#     assert next(objs).name.str == "B"
#     assert next(objs).name.str == "c"
#     assert next(objs).name.str == "a"
#     assert next(objs).name.str == "m"
#     assert next(objs).name.str == "n"


# def test_iter_objects_predicate():
#     module = load_module("mkapi.plugins")
#     assert isinstance(module, Module)
#     cls = get_by_name(module.classes, "MkAPIPlugin")
#     assert isinstance(cls, Class)
#     x = list(iter_objects(cls))
#     members = ["MkAPIPlugin", "on_nav", "pages"]
#     others = ["load_config", "config"]
#     for name in members:
#         assert get_by_name(x, name)
#     for name in others:
#         assert get_by_name(x, name)

#     def predicate(obj, parent):
#         if parent is None:
#             return True
#         return obj.module is parent.module

#     x = list(iter_objects(cls, predicate=predicate))
#     for name in members:
#         assert get_by_name(x, name)
#     for name in others:
#         assert not get_by_name(x, name)


# def test_kind():
#     node = get_module_node("mkapi")
#     assert node
#     module = create_module("mkapi", node)
#     assert module.kind == "package"
#     node = get_module_node("mkapi.objects")
#     assert node
#     module = create_module("mkapi.objects", node)
#     assert module
#     assert module.kind == "module"
#     cls = get_by_name(module.classes, "Object")
#     assert cls
#     assert cls.kind == "dataclass"
#     func = get_by_name(module.functions, "create_function")
#     assert func
#     assert func.kind == "function"
#     method = get_by_name(cls.functions, "__post_init__")
#     assert method
#     assert method.kind == "method"
#     attr = get_by_name(cls.attributes, "node")
#     assert attr
#     assert attr.kind == "attribute"
