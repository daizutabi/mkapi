import ast

from mkapi.objects import Function, create_function
from mkapi.utils import get_by_name


def test_create_function(get):
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
    assert repr(func) == "Function('module_level_function')"


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
#     node = ast.parse(src).body[1]
#     assert isinstance(node, ast.FunctionDef)
#     func = create_function(node)
#     assert get_by_name(func.parameters, "x")
#     assert get_by_name(func.parameters, "y")
#     assert not get_by_name(func.parameters, "z")
#     items = get_by_name(func.doc.sections, "Parameters").items  # type: ignore
#     assert get_by_name(items, "x")
#     assert not get_by_name(items, "y")
#     assert get_by_name(items, "z")
#     assert [item.name.str for item in items] == ["x", "z"]
#     assert func.returns[0].type
#     items = get_by_name(func.doc.sections, "Returns").items  # type: ignore
#     assert items[0].text.str == "Return True."
#     assert items[0].type.expr.id == "bool"  # type: ignore
