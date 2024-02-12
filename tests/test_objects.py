import ast
import inspect
import re
import sys
from pathlib import Path

import pytest

from mkapi.ast import iter_child_nodes
from mkapi.importlib import load_module
from mkapi.objects import (
    LINK_PATTERN,
    Class,
    Function,
    Module,
    create_class,
    create_function,
    create_module,
    iter_objects,
    merge_items,
    objects,
)
from mkapi.utils import get_by_name, get_module_node


@pytest.fixture(scope="module")
def google():
    path = str(Path(__file__).parent)
    if path not in sys.path:
        sys.path.insert(0, str(path))
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


def test_create_function(get):
    node = get("module_level_function")
    assert isinstance(node, ast.FunctionDef)
    func = create_function(node)
    assert isinstance(func, Function)
    assert func.name == "module_level_function"
    assert func.qualname == "module_level_function"
    assert func.fullname == "__mkapi__.module_level_function"
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
    assert cls.name == "ExampleClass"
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
    assert func.qualname == "ExampleClass.__init__"
    assert func.fullname == "__mkapi__.ExampleClass.__init__"
    assert repr(cls) == "Class('ExampleClass')"


def test_create_class_nested():
    src = """
    class A:
        class B:
            class C:
                pass
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node)
    assert len(cls.classes) == 1
    assert len(cls.classes[0].classes) == 1


def test_create_module(google):
    module = create_module("google", google)
    assert module.name == "google"
    assert len(module.functions) == 4
    assert len(module.classes) == 3
    cls = get_by_name(module.classes, "ExampleClass")
    assert isinstance(cls, Class)
    assert cls.fullname == "google.ExampleClass"
    func = get_by_name(cls.functions, "example_method")
    assert isinstance(func, Function)
    assert func.fullname == "google.ExampleClass.example_method"
    assert repr(module) == "Module('google')"


def test_fullname(google):
    module = create_module("examples.styles.google", google)
    c = get_by_name(module.classes, "ExampleClass")
    assert isinstance(c, Class)
    f = get_by_name(c.functions, "example_method")
    assert isinstance(f, Function)
    assert c.fullname == "examples.styles.google.ExampleClass"
    name = "examples.styles.google.ExampleClass.example_method"
    assert f.fullname == name


def test_attribute_comment():
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
    src = inspect.cleandoc(src)
    node = ast.parse(src)
    module = create_module("a", node, src)
    t = module.attributes[0].doc.text.str
    assert t == "Doc comment *inline* with attribute."
    a = module.classes[0].attributes
    assert a[0].doc.text.str == "Doc comment *inline* with attribute."
    assert a[1].doc.text.str
    assert a[1].doc.text.str.startswith("Doc comment *before* attribute, with")
    assert isinstance(a[1].type.expr, ast.Subscript)
    assert a[2].doc.text.str is None
    assert a[3].doc.text.str == "Doc comment *inline* with attribute."
    assert isinstance(a[3].type.expr, ast.Subscript)
    assert a[4].doc.text.str == "Docstring *after* attribute, with type specified."
    assert a[5].doc.text.str is None


def test_merge_items():
    """'''test'''
    def f(x: int = 0, y: str = 's') -> bool:
        '''function.

        Args:
            x: parameter x.
            z: parameter z.

        Returns:
            Return True.'''
    """
    src = inspect.getdoc(test_merge_items)
    assert src
    node = ast.parse(src)
    module = create_module("x", node)
    func = get_by_name(module.functions, "f")
    assert func
    # merge_parameters(func)
    assert get_by_name(func.parameters, "x")
    assert get_by_name(func.parameters, "y")
    assert not get_by_name(func.parameters, "z")
    items = get_by_name(func.doc.sections, "Parameters").items  # type: ignore
    assert get_by_name(items, "x")
    assert not get_by_name(items, "y")
    assert get_by_name(items, "z")
    assert [item.name for item in items] == ["x", "z"]
    # merge_returns(func)
    assert func.returns[0].type
    assert func.returns[0].text.str == "Return True."
    item = get_by_name(func.doc.sections, "Returns").items[0]  # type: ignore
    assert item.type.expr.id == "bool"  # type: ignore


def test_iter_objects():
    """'''test module.'''
    m: str
    n = 1
    '''int: attribute n.'''
    class A(D):
        '''class.

        Attributes:
            a: attribute a.
        '''
        a: int
        def f(x: int, y: str) -> list[str]:
            '''function.'''
            class B(E,F.G):
                c: list
            raise ValueError
    """
    src = inspect.getdoc(test_iter_objects)
    assert src
    node = ast.parse(src)
    module = create_module("x", node)
    cls = get_by_name(module.classes, "A")
    assert cls
    func = get_by_name(cls.functions, "f")
    assert func
    cls = get_by_name(func.classes, "B")
    assert cls
    assert cls.fullname == "x.A.f.B"
    objs = iter_objects(module)
    assert next(objs).name == "x"
    assert next(objs).name == "A"
    assert next(objs).name == "f"
    assert next(objs).name == "B"
    assert next(objs).name == "c"
    assert next(objs).name == "a"
    assert next(objs).name == "m"
    assert next(objs).name == "n"
    merge_items(module)


def test_link_pattern():
    def f(m: re.Match) -> str:
        name = m.group(1)
        if name == "abc":
            return f"[{name}][_{name}]"
        return m.group()

    assert re.search(LINK_PATTERN, "X[abc]Y")
    assert not re.search(LINK_PATTERN, "X[ab c]Y")
    assert re.search(LINK_PATTERN, "X[abc][]Y")
    assert not re.search(LINK_PATTERN, "X[abc](xyz)Y")
    assert not re.search(LINK_PATTERN, "X[abc][xyz]Y")
    assert re.sub(LINK_PATTERN, f, "X[abc]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc[abc]]Y") == "X[abc[abc][_abc]]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab]Y") == "X[ab]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab c]Y") == "X[ab c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc] c]Y") == "X[abc][_abc] c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc](xyz)Y") == "X[abc](xyz)Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][xyz]Y") == "X[abc][xyz]Y"


def test_set_markdown():
    name = "mkapi.plugins"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    x = module.doc.type.markdown
    assert x == "[mkapi][__mkapi__.mkapi]..[plugins][__mkapi__.mkapi.plugins]"
    obj = get_by_name(module.classes, "MkAPIPlugin")
    assert isinstance(obj, Class)
    m = obj.doc.type.markdown
    assert "[mkapi][__mkapi__.mkapi].." in m
    assert "..[plugins][__mkapi__.mkapi.plugins].." in m
    m = obj.bases[0].type.markdown
    assert "[BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin]" in m
    assert "[[MkAPIConfig][__mkapi__.mkapi.plugins.MkAPIConfig]]" in m
    name = "mkapi.items"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    obj = get_by_name(module.functions, "iter_raises")
    assert isinstance(obj, Function)
    m = obj.doc.text.markdown
    assert m == "Yield [Raise][__mkapi__.mkapi.items.Raise] instances."


def test_iter_objects_predicate():
    module = load_module("mkapi.plugins")
    assert isinstance(module, Module)
    cls = get_by_name(module.classes, "MkAPIPlugin")
    assert isinstance(cls, Class)
    x = list(iter_objects(cls))
    members = ["MkAPIPlugin", "on_nav", "pages"]
    others = ["load_config", "config"]
    for name in members:
        assert get_by_name(x, name)
    for name in others:
        assert get_by_name(x, name)

    def predicate(obj, parent):
        if parent is None:
            return True
        return obj.module is parent.module

    x = list(iter_objects(cls, predicate=predicate))
    for name in members:
        assert get_by_name(x, name)
    for name in others:
        assert not get_by_name(x, name)


def test_kind():
    node = get_module_node("mkapi")
    assert node
    module = create_module("mkapi", node)
    assert module.kind == "package"
    node = get_module_node("mkapi.objects")
    assert node
    module = create_module("mkapi.objects", node)
    assert module
    assert module.kind == "module"
    cls = get_by_name(module.classes, "Object")
    assert cls
    assert cls.kind == "dataclass"
    func = get_by_name(module.functions, "create_function")
    assert func
    assert func.kind == "function"
    method = get_by_name(cls.functions, "__post_init__")
    assert method
    assert method.kind == "method"
    attr = get_by_name(cls.attributes, "node")
    assert attr
    assert attr.kind == "attribute"
