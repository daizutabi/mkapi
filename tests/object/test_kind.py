from mkapi.object import get_object


def test_object_kind_async_function():
    obj = get_object("examples.object.async_function")
    assert obj
    assert obj.kind == "async function"


def test_object_kind_async_method():
    obj = get_object("examples.object.Kind.async_method")
    assert obj
    assert obj.kind == "async method"


def test_object_kind_classmethod():
    obj = get_object("examples.object.Kind.class_method")
    assert obj
    assert obj.kind == "classmethod"


def test_object_kind_staticmethod():
    obj = get_object("examples.object.Kind.static_method")
    assert obj
    assert obj.kind == "staticmethod"


def test_object_kind_async_classmethod():
    obj = get_object("examples.object.Kind.async_class_method")
    assert obj
    assert obj.kind == "async classmethod"


def test_object_kind_async_staticmethod():
    obj = get_object("examples.object.Kind.async_static_method")
    assert obj
    assert obj.kind == "async staticmethod"
