"""This modules provides Module class that has tree structure."""
import inspect
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mkapi.core.node import Node, get_node
from mkapi.core.node import get_members as get_node_members
from mkapi.core.object import get_object
from mkapi.core.structure import Tree


@dataclass(repr=False)
class Module(Tree):
    """Module class represents a module.

    Attributes:
        parent: Parent Module instance.
        members: Member Module instances.
        node: Node inspect of self.
    """

    parent: Optional["Module"] = field(default=None, init=False)
    members: list["Module"] = field(init=False)
    node: Node = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.node = get_node(self.obj)

    def __iter__(self) -> Iterator["Module"]:
        if self.docstring:  # noqa: SIM114
            yield self
        elif self.object.kind in ["package", "module"] and any(
            m.docstring for m in self.members
        ):
            yield self
        if self.object.kind == "package":
            for member in self.members:
                yield from member

    def get_kind(self) -> str:  # noqa: D102
        if not self.sourcefile or self.sourcefile.endswith("__init__.py"):
            return "package"
        return "module"

    def get_members(self) -> list:  # noqa: D102
        if self.object.kind == "module":
            return get_node_members(self.obj)
        return get_members(self.obj)

    def get_markdown(self, filters: list[str]) -> str:
        """Return a Markdown source for docstring of this object.

        Args:
            filters: A list of filters. Avaiable filters: `upper`, `inherit`,
                `strict`.
        """
        from mkapi.core.renderer import renderer

        return renderer.render_module(self, filters)


def get_members(obj: object) -> list[Module]:
    """Return members."""
    try:
        sourcefile = inspect.getsourcefile(obj)  # type: ignore
    except TypeError:
        return []
    if not sourcefile:
        return []
    root = Path(sourcefile).parent
    paths = [path for path in os.listdir(root) if not path.startswith("_")]
    members = []
    for path in paths:
        root_ = root / path
        name = ""
        if Path.is_dir(root_) and "__init__.py" in os.listdir(root_):
            name = path
        elif path.endswith(".py"):
            name = path[:-3]
        if name:
            name = f"{obj.__name__}.{name}"
            module = get_module(name)
            members.append(module)
    packages = []
    modules = []
    for member in members:
        if member.object.kind == "package":
            packages.append(member)
        else:
            modules.append(member)
    return modules + packages


modules: dict[str, Module] = {}


def get_module(name: str) -> Module:
    """Return a Module instace by name or object.

    Args:
        name: Object name or object itself.
    """
    obj = get_object(name) if isinstance(name, str) else name
    name = obj.__name__
    if name in modules:
        return modules[name]
    module = Module(obj)
    modules[name] = module
    return module
