import inspect
import os
from dataclasses import dataclass, field
from typing import Iterator, List

from mkapi.core.node import get_kind
from mkapi.core.object import get_object, get_sourcefile_and_lineno
from mkapi.core.renderer import renderer
from mkapi.core.tree import Tree


@dataclass
class Module(Tree):
    """Module class represents an module.

    Attributes:
        kind: Kind. `package` or `module`.
    """

    members: List["Module"] = field(init=False)
    objects: List[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        super().__post_init__()
        if self.object.kind == "module":
            objects = get_objects(self.obj)
            self.objects = [".".join([self.object.id, obj]) for obj in objects]

    def __iter__(self) -> Iterator["Module"]:
        if self.docstring:
            yield self
        elif self.object.kind == "package" and any(m.docstring for m in self.members):
            yield self
        for member in self.members:
            yield from member

    def get_kind(self) -> str:
        if not self.sourcefile or self.sourcefile.endswith("__init__.py"):
            return "package"
        else:
            return "module"

    def get_members(self) -> List["Module"]:  # type:ignore
        if self.object.kind == "module":
            return []
        else:
            return get_members(self.obj)

    def get_markdown(self) -> str:
        """Returns a Markdown source for docstring of this object."""
        return renderer.render_module(self)


def get_objects(obj) -> List[str]:
    obj_source_file = inspect.getsourcefile(obj)
    members = []
    for name, obj in inspect.getmembers(obj):
        if name.startswith("_"):
            continue
        if not get_kind(obj):
            continue
        sourcefile, lineno = get_sourcefile_and_lineno(obj)
        if sourcefile != obj_source_file:
            continue
        if not inspect.getdoc(obj):
            continue
        members.append((name, lineno))
    members = sorted(members, key=lambda x: x[1])
    return [x[0] for x in members]


def get_members(obj) -> List[Module]:
    sourcefile = inspect.getsourcefile(obj)
    if not sourcefile:
        return []
    root = os.path.dirname(sourcefile)
    paths = [path for path in os.listdir(root) if not path.startswith("_")]
    members = []
    for path in paths:
        root_ = os.path.join(root, path)
        name = ""
        if os.path.isdir(root_) and "__init__.py" in os.listdir(root_):
            name = path
        elif path.endswith(".py"):
            name = path[:-3]
        if name:
            name = ".".join([obj.__name__, name])
            module = get_module(name)
            members.append(module)
    return members


def get_module(name) -> Module:
    if isinstance(name, str):
        obj = get_object(name)
    else:
        obj = name

    return Module(obj)
