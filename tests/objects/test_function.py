import ast
import inspect

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
    # assert len(func.raises) == 1
    assert len(func.raises) == 0
    assert len(func.doc.sections) == 3
    assert repr(func) == "Function('module_level_function')"
    section = get_by_name(func.doc.sections, "Parameters")
    assert section
    assert len(section.items) == 4
    section = get_by_name(func.doc.sections, "Returns")
    assert section
    assert len(section.items) == 1
    section = get_by_name(func.doc.sections, "Raises")
    assert section
    assert len(section.items) == 2
    t = section.items[0].type.expr
    assert t
    assert ast.unparse(t) == "'AttributeError'"
    t = section.items[1].type.expr
    assert t
    assert ast.unparse(t) == "'ValueError'"


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
    node = ast.parse(src).body[1]
    assert isinstance(node, ast.FunctionDef)
    func = create_function(node)
    assert get_by_name(func.parameters, "x")
    assert get_by_name(func.parameters, "y")
    assert not get_by_name(func.parameters, "z")
    items = get_by_name(func.doc.sections, "Parameters").items  # type: ignore
    assert get_by_name(items, "x")
    assert not get_by_name(items, "y")
    assert get_by_name(items, "z")
    assert [item.name.str for item in items] == ["x", "z"]
    assert func.returns[0].type
    items = get_by_name(func.doc.sections, "Returns").items  # type: ignore
    assert items[0].text.str == "Return True."
    assert items[0].type.expr.id == "bool"  # type: ignore
