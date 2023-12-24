from dataclasses import dataclass

from mkapi.core.base import Type


@dataclass
class Base:
    """Base class."""

    name: str  #: Object name.
    type: Type  #: Object type.  # noqa: A003

    def set_name(self, name: str):
        """Set name.

        Args:
            name: A New name.
        """
        self.name = name


@dataclass
class Item(Base):
    """Item class."""

    markdown: str  #: Object Markdown.

    def set_name(self, name: str):
        """Set name in upper case."""
        self.name = name.upper()
