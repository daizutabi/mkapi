"""Objects."""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any


@dataclass
class Object:
    """Object class."""

    name: str  # Qualified module name.
    obj: object  # Object.
    members: dict[str, Any]  # Members of the object.

    def __post_init__(self) -> None:
        pass

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name})"

    def update(self) -> None:
        """Update contents."""


def get_members(obj: object) -> dict[str, Any]:
    """Return pulblic members of an object as a (name => value) dictionary."""
    members = {}
    for name, member in inspect.getmembers(obj):
        if not name.startswith("_"):
            members[name] = member
    return members
