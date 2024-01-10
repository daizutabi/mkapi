import ast
import importlib
import inspect

from mkapi.dataclasses import is_dataclass
from mkapi.objects import Attribute, Class, Parameter, get_object


def test_parameters():
    cls = get_object("mkapi.objects.Class")
    assert isinstance(cls, Class)
    assert is_dataclass(cls)
    modulename = cls.modulename
    assert modulename
    module_obj = importlib.import_module(modulename)
    members = dict(inspect.getmembers(module_obj, inspect.isclass))
    assert cls.name
    cls_obj = members[cls.name]
    params = inspect.signature(cls_obj).parameters
    bases = list(cls.iter_bases())
    attrs: dict[str, Attribute] = {}
    for base in bases:
        if not is_dataclass(base):
            raise NotImplementedError
        for attr in base.attributes:
            attrs[attr.name] = attr  # updated by subclasses.
    ps = []
    for p in params.values():
        if p.name not in attrs:
            raise NotImplementedError
        attr = attrs[p.name]
        args = (None, p.name, attr.docstring, attr.type, attr.default, p.kind)
        parameter = Parameter(*args)
        ps.append(parameter)
    cls.parameters = ps
    p = cls.parameters
    assert p[0].name == "_node"
    assert ast.unparse(p[0].type) == "ast.ClassDef"
    assert p[1].name == "name"
    assert ast.unparse(p[1].type) == "str"
    assert p[2].name == "docstring"
    assert ast.unparse(p[2].type) == "Docstring | None"
    assert p[3].name == "parameters"
    assert ast.unparse(p[3].type) == "list[Parameter]"
    assert p[4].name == "raises"
    assert ast.unparse(p[4].type) == "list[Raise]"
    assert p[5].name == "decorators"
    assert ast.unparse(p[5].type) == "list[ast.expr]"
    assert p[6].name == "type_params"
    assert ast.unparse(p[6].type) == "list[ast.type_param]"
    # assert p[7].name == "parent"
    # assert ast.unparse(p[7].type) == "Class | Module | None"
    assert p[7].name == "attributes"
    assert ast.unparse(p[7].type) == "list[Attribute]"
    assert p[8].name == "classes"
    assert ast.unparse(p[8].type) == "list[Class]"
    assert p[9].name == "functions"
    assert ast.unparse(p[9].type) == "list[Function]"
    assert p[10].name == "bases"
    assert ast.unparse(p[10].type) == "list[Class]"
