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
    type: Type


@dataclass
class Item(Base):
    """Item class.

    Parameters:
        markdown: Object markdown

    Attributes:
        markdown: Object markdown
    """

    markdown: str
