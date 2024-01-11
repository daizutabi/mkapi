import ast

from mkapi.dataclasses import is_dataclass
from mkapi.objects import Class, Parameter, get_object


def test_parameters():
    cls = get_object("mkapi.objects.Class")
    assert isinstance(cls, Class)
    assert is_dataclass(cls)
    p = cls.parameters
    assert len(p) == 10
    assert p[0].name == "node"
    assert p[0].type
    assert ast.unparse(p[0].type.expr) == "ast.ClassDef"
    assert p[1].name == "name"
    assert p[1].type
    assert ast.unparse(p[1].type.expr) == "str"
    assert p[2].name == "_text"
    assert p[2].type
    assert (
        ast.unparse(p[2].type.expr) == "InitVar[str | None]"
    )  # TODO: Delete `InitVar`
    assert p[3].name == "_type"
    assert p[3].type
    assert (
        ast.unparse(p[3].type.expr) == "InitVar[ast.expr | None]"
    )  # TODO: Delete `InitVar`
    assert p[4].name == "parameters"
    assert p[4].type
    assert ast.unparse(p[4].type.expr) == "list[Parameter]"
    assert p[5].name == "raises"
    assert p[5].type
    assert ast.unparse(p[5].type.expr) == "list[Raise]"
    assert p[6].name == "attributes"
    assert p[6].type
    assert ast.unparse(p[6].type.expr) == "list[Attribute]"
    assert p[7].name == "classes"
    assert p[7].type
    assert ast.unparse(p[7].type.expr) == "list[Class]"
    assert p[8].name == "functions"
    assert p[8].type
    assert ast.unparse(p[8].type.expr) == "list[Function]"
    assert p[9].name == "bases"
    assert p[9].type
    assert ast.unparse(p[9].type.expr) == "list[Class]"
