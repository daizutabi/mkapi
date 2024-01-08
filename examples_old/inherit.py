from dataclasses import dataclass

from mkapi.core.base import Type


@dataclass
class Base:
    """Base class.

    Parameters:
        name: Object name.

    Attributes:
        name: Object name.
    """

    name: str
    type: Type  # noqa: A003

    def set_name(self, name: str):
        """Set name.

        Args:
            name: A New name.
        """
        self.name = name

    def get(self):
        """Return {class} instace."""
        return self


@dataclass
class Item(Base):
    """Item class.

    Parameters:
        markdown: Object markdown.

    Attributes:
        markdown: Object markdown.
    """

    markdown: str

    def set_name(self, name: str):
        """Set name in upper case."""
        self.name = name.upper()
