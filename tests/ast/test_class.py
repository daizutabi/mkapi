import ast
import inspect


def test_class():
    src = """
    class C(B):
        '''docstring.'''
        a:str # attr a.
        b:str='c'
        '''attr b.

        ade
        '''
        c
    """
    node = ast.parse(src := inspect.cleandoc(src)).body[0]
    assert isinstance(node, ast.ClassDef)
    assert node.name == "C"
    assert isinstance(bases := node.bases, list)
    assert isinstance(bases[0], ast.Name)
    assert bases[0].id == "B"
    assert isinstance(body := node.body, list)
    assert isinstance(body[0], ast.Expr)
    assert isinstance(c := body[0].value, ast.Constant)
    assert c.value == "docstring."
    assert isinstance(a := body[1], ast.AnnAssign)
    assert a.target.id == "a"  # type: ignore
    assert a.value is None
    assert a.annotation.id == "str"  # type: ignore
    assert a.lineno == 3
    assert (a.lineno, a.col_offset, a.end_col_offset) == (3, 4, 9)
    line = src.split("\n")[2]
    assert line[4:9] == "a:str"
    assert line[9:] == " # attr a."
    assert isinstance(a := body[2], ast.AnnAssign)
    assert a.target.id == "b"  # type: ignore
    assert a.value.value == "c"  # type: ignore
    assert isinstance(body[3], ast.Expr)
    assert isinstance(c := body[3].value, ast.Constant)
    assert inspect.cleandoc(c.value) == "attr b.\n\nade"
    assert isinstance(body[4], ast.Expr)
    assert isinstance(body[4].value, ast.Name)
    assert body[4].value.id == "c"
    assert body[4].lineno == 9
