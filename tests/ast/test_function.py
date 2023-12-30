import ast
import inspect


def test_function():
    src = """
    def f(a,b:str,/,c:list[int],d:tuple[int,...]="x",*,e=4)->float:
        '''docstring.'''
        return 1.0
    """
    node = ast.parse(inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.FunctionDef)
    assert node.name == "f"
    assert isinstance(args := node.args.posonlyargs, list)
    assert len(args) == 2
    assert isinstance(args[0], ast.arg)
    assert args[0].arg == "a"
    assert args[0].annotation is None
    assert args[1].arg == "b"
    assert isinstance(ann := args[1].annotation, ast.Name)
    assert ann.id == "str"
    assert isinstance(args := node.args.args, list)
    assert len(args) == 2
    assert isinstance(args[0], ast.arg)
    assert args[0].arg == "c"
    assert isinstance(ann := args[0].annotation, ast.Subscript)
    assert isinstance(ann.value, ast.Name)
    assert ann.value.id == "list"
    assert isinstance(ann.slice, ast.Name)
    assert ann.slice.id == "int"
    assert args[1].arg == "d"
    assert isinstance(ann := args[1].annotation, ast.Subscript)
    assert isinstance(ann.value, ast.Name)
    assert ann.value.id == "tuple"
    assert isinstance(ann.slice, ast.Tuple)
    assert isinstance(elts := ann.slice.elts, list)
    assert isinstance(elts[0], ast.Name)
    assert isinstance(elts[1], ast.Constant)
    assert elts[1].value is Ellipsis
    assert node.args.vararg is None
    assert isinstance(args := node.args.kwonlyargs, list)
    assert isinstance(args[0], ast.arg)
    assert node.args.kwarg is None
    assert node.args.defaults[0].value == "x"  # type: ignore
    assert node.args.kw_defaults[0].value == 4  # type: ignore
    assert isinstance(r := node.returns, ast.Name)
    assert r.id == "float"
    assert ast.get_docstring(node) == "docstring."
