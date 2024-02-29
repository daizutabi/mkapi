import ast


def test_create_function(get):
    from mkapi.objects import Function, create_function
    from mkapi.utils import get_by_name

    node = get("module_level_function")
    assert isinstance(node, ast.FunctionDef)
    func = create_function(node, "", None)
    assert isinstance(func, Function)
    assert func.name == "module_level_function"
    assert func.qualname == "module_level_function"
    assert len(func.parameters) == 4
    assert get_by_name(func.parameters, "param1")
    assert get_by_name(func.parameters, "param2")
    assert get_by_name(func.parameters, "args")
    assert get_by_name(func.parameters, "kwargs")
    assert len(func.raises) == 1
