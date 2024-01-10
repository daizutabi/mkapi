import ast

from mkapi.dataclasses import is_dataclass
from mkapi.objects import Class, get_object


def test_parameters():
    cls = get_object("mkapi.objects.Class")
    assert isinstance(cls, Class)
    assert is_dataclass(cls)
    p = cls.parameters
    assert len(p) == 11
    assert p[0].name == "_node"
    assert p[0].type
    assert ast.unparse(p[0].type) == "ast.ClassDef"
    assert p[1].name == "name"
    assert p[1].type
    assert ast.unparse(p[1].type) == "str"
    assert p[2].name == "docstring"
    assert p[2].type
    assert ast.unparse(p[2].type) == "Docstring | None"
    assert p[3].name == "parameters"
    assert p[3].type
    assert ast.unparse(p[3].type) == "list[Parameter]"
    assert p[4].name == "raises"
    assert p[4].type
    assert ast.unparse(p[4].type) == "list[Raise]"
    assert p[5].name == "decorators"
    assert p[5].type
    assert ast.unparse(p[5].type) == "list[ast.expr]"
    assert p[6].name == "type_params"
    assert p[6].type
    assert ast.unparse(p[6].type) == "list[ast.type_param]"
    assert p[7].name == "attributes"
    assert p[7].type
    assert ast.unparse(p[7].type) == "list[Attribute]"
    assert p[8].name == "classes"
    assert p[8].type
    assert ast.unparse(p[8].type) == "list[Class]"
    assert p[9].name == "functions"
    assert p[9].type
    assert ast.unparse(p[9].type) == "list[Function]"
    assert p[10].name == "bases"
    assert p[10].type
    assert ast.unparse(p[10].type) == "list[Class]"
