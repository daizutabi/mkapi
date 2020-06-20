"""This module provides functions that inspect attributes from source code."""
import ast
import importlib
import inspect
from dataclasses import InitVar, is_dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Tuple

import _ast
from mkapi import utils


def parse_attribute(x) -> str:
    return ".".join([parse_node(x.value), x.attr])


def parse_attribute_with_lineno(x) -> Tuple[str, int]:
    return parse_node(x), x.lineno


def parse_subscript(x) -> str:
    value = parse_node(x.value)
    slice = parse_node(x.slice.value)
    if isinstance(slice, str):
        return f"{value}[{slice}]"
    else:
        slice = ", ".join(slice)
        return f"{value}[{slice}]"


def parse_tuple(x):
    return tuple(parse_node(x) for x in x.elts)


def parse_list(x):
    return "[" + ", ".join(parse_node(x) for x in x.elts) + "]"


def parse_node(x):
    if isinstance(x, _ast.Name):
        return x.id
    elif isinstance(x, _ast.Assign):
        return parse_node(x.targets[0])
    elif isinstance(x, _ast.Attribute):
        return parse_attribute(x)
    elif isinstance(x, _ast.Subscript):
        return parse_subscript(x)
    elif isinstance(x, _ast.Tuple):
        return parse_tuple(x)
    elif isinstance(x, _ast.List):
        return parse_list(x)
    elif hasattr(_ast, "Constant") and isinstance(x, _ast.Constant):
        return x.value
    elif hasattr(_ast, "Str") and isinstance(x, _ast.Str):
        return x.s
    else:
        raise NotImplementedError


def parse_annotation_assign(assign) -> Tuple[str, int, str]:
    type = parse_node(assign.annotation)
    attr, lineno = parse_attribute_with_lineno(assign.target)
    return attr, lineno, type


def get_description(lines: List[str], lineno: int) -> str:
    index = lineno - 1
    line = lines[index]
    if "  #: " in line:
        return line.split("  #: ")[1].strip()
    if index != 0:
        line = lines[index - 1].strip()
        if line.startswith("#: "):
            return line[3:].strip()
    if index + 1 < len(lines):
        docs = []
        in_doc = False
        for line in lines[index + 1 :]:
            line = line.strip()
            if not in_doc and not line:
                break
            elif not in_doc and (line.startswith("'''") or line.startswith('"""')):
                mark = line[:3]
                if line.endswith(mark):
                    return line[3:-3]
                in_doc = True
                docs.append(line[3:])
            elif in_doc and line.endswith(mark):
                docs.append(line[:-3])
                return "\n".join(docs).strip()
            elif in_doc:
                docs.append(line)
    return ""


def get_source(obj) -> str:
    try:
        source = inspect.getsource(obj) or ""
        if not source:
            return ""
    except (OSError, TypeError):
        return ""
    else:
        return source


def get_attributes_with_lineno(
    nodes: Iterable[ast.AST], module, is_module: bool = False
) -> List[Tuple[str, int, Any]]:
    attr_dict: Dict[Tuple[str, int], Any] = {}
    linenos: Dict[int, int] = {}

    def update(attr, lineno, type):
        if type or (attr, lineno) not in attr_dict:
            attr_dict[(attr, lineno)] = type
            linenos[lineno] = linenos.get(lineno, 0) + 1

    globals = dict(inspect.getmembers(module))
    for x in nodes:
        if isinstance(x, _ast.AnnAssign):
            attr, lineno, type_str = parse_annotation_assign(x)
            try:
                type = eval(type_str, globals)
            except NameError:
                type = type_str
            update(attr, lineno, type)
        if isinstance(x, _ast.Attribute) and isinstance(x.ctx, _ast.Store):
            attr, lineno = parse_attribute_with_lineno(x)
            update(attr, lineno, ())
        if is_module and isinstance(x, _ast.Assign):
            attr, lineno = parse_attribute_with_lineno(x)
            update(attr, lineno, ())
    attr_lineno = [(attr, lineno, type) for (attr, lineno), type in attr_dict.items()]
    attr_lineno = [x for x in attr_lineno if linenos[x[1]] == 1]
    attr_lineno = sorted(attr_lineno, key=lambda x: x[1])
    return attr_lineno


def get_attributes_dict(
    attr_list: List[Tuple[str, int, Any]], source: str, prefix: str = ""
) -> Dict[str, Tuple[Any, str]]:

    attrs: Dict[str, Tuple[Any, str]] = {}
    lines = source.split("\n")
    for k, (name, lineno, type) in enumerate(attr_list):
        if not prefix or name.startswith(prefix):
            name = name[len(prefix) :]
            stop = len(lines)
            if k < len(attr_list) - 1:
                stop = attr_list[k + 1][1] - 1
            description = get_description(lines[:stop], lineno)
            if type:
                attrs[name] = type, description  # Assignment with type annotation wins.
            elif name not in attrs:
                attrs[name] = None, description
    return attrs


def get_class_attributes(cls) -> Dict[str, Tuple[Any, str]]:
    """Returns a dictionary that maps attribute name to a tuple of
    (type, description).

    Args:
        cls: Class object.

    Examples:
        >>> from examples.google_style import ExampleClass
        >>> attrs = get_class_attributes(ExampleClass)
        >>> attrs['a'][0] is str
        True
        >>> attrs['a'][1]
        'The first attribute. Comment *inline* with attribute.'
        >>> attrs['b'][0] == Dict[str, int]
        True
        >>> attrs['c'][0] is None
        True
    """
    source = get_source(cls)
    if not source:
        return {}
    source = utils.join(source.split("\n"))
    node = ast.parse(source)
    nodes = ast.walk(node)
    module = importlib.import_module(cls.__module__)
    attr_lineno = get_attributes_with_lineno(nodes, module)
    return get_attributes_dict(attr_lineno, source, prefix="self.")


def get_dataclass_attributes(cls) -> Dict[str, Tuple[Any, str]]:
    """Returns a dictionary that maps attribute name to a tuple of
    (type, description).

    Args:
        cls: Dataclass object.

    Examples:
        >>> from mkapi.core.base import Item, Type, Inline
        >>> attrs = get_dataclass_attributes(Item)
        >>> attrs['type'][0] is Type
        True
        >>> attrs['description'][0] is Inline
        True
    """
    fields = cls.__dataclass_fields__.values()
    attrs = {}
    for field in fields:
        if field.type != InitVar:
            attrs[field.name] = field.type, ""

    source = get_source(cls)
    source = utils.join(source.split("\n"))
    if not source:
        return {}
    node = ast.parse(source).body[0]

    def nodes():
        for x in ast.iter_child_nodes(node):
            if isinstance(x, _ast.FunctionDef):
                break
            yield x

    module = importlib.import_module(cls.__module__)
    attr_lineno = get_attributes_with_lineno(nodes(), module)
    for name, (type, description) in get_attributes_dict(attr_lineno, source).items():
        if name in attrs:
            attrs[name] = attrs[name][0], description
        else:
            attrs[name] = type, description

    return attrs


def get_module_attributes(module) -> Dict[str, Tuple[Any, str]]:
    """Returns a dictionary that maps attribute name to a tuple of
    (type, description).

    Args:
        module: Module object.

    Examples:
        >>> from mkapi.core import renderer
        >>> attrs = get_module_attributes(renderer)
        >>> attrs['renderer'][0] is renderer.Renderer
        True
    """
    source = get_source(module)
    if not source:
        return {}
    node = ast.parse(source)
    nodes = ast.iter_child_nodes(node)
    attr_lineno = get_attributes_with_lineno(nodes, module, is_module=True)
    return get_attributes_dict(attr_lineno, source)


@lru_cache(maxsize=1000)
def get_attributes(obj) -> Dict[str, Tuple[Any, str]]:
    """Returns a dictionary that maps attribute name to
    a tuple of (type, description).

    Args:
        obj: Object.

    See Alse:
        get_class_attributes_, get_dataclass_attributes_, get_module_attributes_.
    """
    if is_dataclass(obj):
        return get_dataclass_attributes(obj)
    elif inspect.isclass(obj):
        return get_class_attributes(obj)
    elif inspect.ismodule(obj):
        return get_module_attributes(obj)
    return {}
