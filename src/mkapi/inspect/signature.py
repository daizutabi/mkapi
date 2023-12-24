"""Signature class that inspects object and creates signature and types."""
import inspect
from dataclasses import InitVar, dataclass, field, is_dataclass
from functools import lru_cache
from typing import Any

from mkapi.core import preprocess
from mkapi.core.attribute import get_attributes
from mkapi.core.base import Inline, Item, Section, Type
from mkapi.inspect.typing import to_string


@dataclass
class Signature:
    """Signature class.

    Args:
        obj: Object

    Attributes:
        signature: `inspect.Signature` instance.
        parameters: Parameters section.
        defaults: Default value dictionary. Key is parameter name and
            value is default value.
        attributes: Attributes section.
        returns: Returned type string. Used in Returns section.
        yields: Yielded type string. Used in Yields section.
    """

    obj: Any = field(default=None, repr=False)
    signature: inspect.Signature | None = field(default=None, init=False)
    parameters: Section = field(default_factory=Section, init=False)
    defaults: dict[str, Any] = field(default_factory=dict, init=False)
    attributes: Section = field(default_factory=Section, init=False)
    returns: str = field(default="", init=False)
    yields: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.obj is None:
            return
        try:
            self.signature = inspect.signature(self.obj)
        except (TypeError, ValueError):
            self.set_attributes()
            return

        items, self.defaults = get_parameters(self.obj)
        self.parameters = Section("Parameters", items=items)
        self.set_attributes()
        return_type = self.signature.return_annotation
        self.returns = to_string(return_type, kind="returns", obj=self.obj)
        self.yields = to_string(return_type, kind="yields", obj=self.obj)

    def __contains__(self, name: str) -> bool:
        return name in self.parameters

    def __getitem__(self, name: str):  # noqa: ANN204
        return getattr(self, name.lower())

    def __str__(self) -> str:
        args = self.arguments
        return "" if args is None else "(" + ", ".join(args) + ")"

    @property
    def arguments(self) -> list[str] | None:
        """Returns arguments list."""
        if self.obj is None or not callable(self.obj):
            return None

        args = []
        for item in self.parameters.items:
            arg = item.name
            if self.defaults[arg] != inspect.Parameter.empty:
                arg += "=" + self.defaults[arg]
            args.append(arg)
        return args

    def set_attributes(self) -> None:
        """Set attributes.

        Examples:
            >>> from mkapi.core.base import Base
            >>> s = Signature(Base)
            >>> s.parameters['name'].to_tuple()
            ('name', 'str, optional', 'Name of self.')
            >>> s.attributes['html'].to_tuple()
            ('html', 'str', 'HTML output after conversion.')
        """
        items = []
        for name, (tp, description) in get_attributes(self.obj).items():
            type_str = to_string(tp, obj=self.obj) if tp else ""
            if not type_str:
                type_str, description = preprocess.split_type(description)  # noqa: PLW2901

            item = Item(name, Type(type_str), Inline(description))
            if is_dataclass(self.obj):
                if name in self.parameters:
                    self.parameters[name].set_description(item.description)
                if self.obj.__dataclass_fields__[name].type != InitVar:
                    items.append(item)
            else:
                items.append(item)
        self.attributes = Section("Attributes", items=items)

    def split(self, sep: str = ",") -> list[str]:
        """Return a list of substring."""
        return str(self).split(sep)


def get_parameters(obj) -> tuple[list[Item], dict[str, Any]]:  # noqa: ANN001
    """Return a tuple of parameters section and defalut values."""
    signature = inspect.signature(obj)
    items: list[Item] = []
    defaults: dict[str, Any] = {}

    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            key = f"*{name}"
        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            key = f"**{name}"
        else:
            key = name
        type_ = to_string(parameter.annotation, obj=obj)
        if (default := parameter.default) == inspect.Parameter.empty:
            defaults[key] = default
        else:
            defaults[key] = f"{default!r}"
            if not type_:
                type_ = "optional"
            elif not type_.endswith(", optional"):
                type_ += ", optional"
        items.append(Item(key, Type(type_)))

    return items, defaults


@lru_cache(maxsize=1000)
def get_signature(obj: object) -> Signature:
    """Return a `Signature` object for `obj`."""
    return Signature(obj)
