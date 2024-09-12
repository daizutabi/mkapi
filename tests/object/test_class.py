import ast
import inspect


def test_create_class_nested():
    from mkapi.object import Class, create_class

    src = """
    class A:
        class B:
            class C:
                pass
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "test_create_class_nested", None)
    assert len(cls.children) == 1
    cls = cls.children["B"]
    assert isinstance(cls, Class)
    assert len(cls.children) == 1
    cls = cls.children["C"]
    assert isinstance(cls, Class)


def test_create_class(get):
    from mkapi.object import Class, Function, Property, create_class

    node = get("ExampleClass")
    assert isinstance(node, ast.ClassDef)
    cls = create_class(node, "test_create_class", None)
    assert isinstance(cls, Class)
    assert cls.name == "ExampleClass"
    assert len(cls.raises) == 0
    for x in ["_private"]:
        assert isinstance(cls.get(x), Function)
    for x in ["readonly_property", "readwrite_property"]:
        assert isinstance(cls.get(x), Property)


def test_inherit():
    from mkapi.object import Class, Function, create_module

    module = create_module("mkapi.object")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    func = cls.get("__repr__")
    assert isinstance(func, Function)
    assert func.qualname == "Object.__repr__"


def test_class_parameters():
    from mkapi.object import Class, create_module
    from mkapi.utils import find_item_by_name

    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    assert len(cls.parameters) == 3
    module = create_module("mkapi.object")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    assert find_item_by_name(cls.parameters, "name")
    assert find_item_by_name(cls.parameters, "node")
    assert find_item_by_name(cls.parameters, "module")
    assert find_item_by_name(cls.parameters, "parent")


def test_inherit_base_classes():
    from mkapi.object import Class, create_module

    module = create_module("mkapi.plugin")
    assert module
    cls = module.get("MkApiConfig")
    assert isinstance(cls, Class)
    assert cls.get("config_file_path")
    cls = module.get("MkApiPlugin")
    assert isinstance(cls, Class)
    assert cls.get("on_page_read_source")
    module = create_module("mkapi.ast")
    assert module
    cls = module.get("Parameter")
    assert isinstance(cls, Class)
    assert cls.get("name")
    assert cls.get("type")
    assert cls.get("default")


def test_iter_dataclass_parameters():
    from mkapi.object import Class, create_module

    module = create_module("mkapi.ast")
    assert module
    cls = module.get("Parameter")
    assert isinstance(cls, Class)
    p = cls.parameters
    assert p[0].name == "name"
    assert p[1].name == "type"
    assert p[2].name == "default"
    assert p[3].name == "kind"


def test_iter_attributes_from_function():
    from mkapi.object import Class, create_module

    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    for k in range(1, 6):
        assert f"attr{k}" in cls.children


def test_type():
    from mkapi.object import Attribute, Class, Property, create_module

    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    x = cls.get("attr4")
    assert isinstance(x, Attribute)
    assert x.type is None
    assert x.doc.type == "list(str)"
    x = cls.get("readonly_property")
    assert isinstance(x, Property)
    assert x.type is None
    assert x.doc.type == "str"


def test_merge_init_doc():
    from mkapi.object import Class, create_module

    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    assert cls.doc.text
    assert len(cls.doc.sections) == 2


def test_children_order():
    from mkapi.object import Class, get_object

    cls = get_object("mkapi.node.Import")
    assert isinstance(cls, Class)
    names = list(cls.children.keys())
    print(names)
    assert names[0] == "name"
    assert names[1] == "node"
    assert names[-1] == "fullname"


def test_enum():
    from mkapi.object import Class, get_object

    cls = get_object("mkapi.page.PageKind")
    assert isinstance(cls, Class)
    names = [name for name, _ in cls.get_children()]
    assert "name" in names
    assert "value" in names
    assert "OBJECT" in names
    assert "SOURCE" in names
    assert "DOCUMENTATION" in names
