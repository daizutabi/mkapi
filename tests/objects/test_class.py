import ast
import inspect


def test_create_class_nested():
    from mkapi.objects import Class, create_class

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
    from mkapi.objects import Class, Function, Property, create_class

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
    from mkapi.objects import Class, Function, create_module

    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    func = cls.get("__repr__")
    assert isinstance(func, Function)
    assert func.qualname == "Object.__repr__"


def test_class_parameters():
    from mkapi.objects import Class, create_module
    from mkapi.utils import get_by_name

    module = create_module("examples.styles.google")
    assert module
    cls = module.get("ExampleClass")
    assert isinstance(cls, Class)
    assert len(cls.parameters) == 3
    module = create_module("mkapi.objects")
    assert module
    cls = module.get("Class")
    assert isinstance(cls, Class)
    assert get_by_name(cls.parameters, "name")
    assert get_by_name(cls.parameters, "node")
    assert get_by_name(cls.parameters, "module")
    assert get_by_name(cls.parameters, "parent")


def test_inherit_base_classes():
    from mkapi.objects import Class, create_module

    module = create_module("mkapi.plugins")
    assert module
    cls = module.get("MkAPIConfig")
    assert isinstance(cls, Class)
    assert cls.get("config_file_path")
    cls = module.get("MkAPIPlugin")
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
    from mkapi.objects import Class, create_module

    module = create_module("mkapi.ast")
    assert module
    cls = module.get("Parameter")
    assert isinstance(cls, Class)
    p = cls.parameters
    assert p[0].name == "name"
    assert p[1].name == "type"
    assert p[2].name == "default"
    assert p[3].name == "kind"
