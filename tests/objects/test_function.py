import ast

from mkapi.objects import Function, create_function, objects
from mkapi.utils import get_by_name


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
