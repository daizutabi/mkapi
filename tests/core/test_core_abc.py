from abc import ABC, abstractmethod

from mkapi.core.node import get_node


class C(ABC):
    """Abstract class."""

    def method(self):
        """Method."""

    @classmethod
    def class_method(cls):
        """Classmethod."""

    @staticmethod
    def static_method():
        """Staticmethod."""

    @abstractmethod
    def abstract_method(self):
        """Abstract method."""

    @classmethod
    @abstractmethod
    def abstract_classmethod(cls):
        """Abstract classmethod."""

    @staticmethod
    @abstractmethod
    def abstract_staticmethod():
        """Abstract staticmethod."""

    @property  # type:ignore
    @abstractmethod
    def abstract_readonly_property(self):
        """Abstract readonly property."""

    @property  # type:ignore
    @abstractmethod
    def abstract_readwrite_property(self):
        """Abstract readwrite property."""

    @abstract_readwrite_property.setter  # type:ignore
    @abstractmethod
    def abstract_readwrite_property(self, val):
        pass


def test_abc():
    node = get_node(C)
    node.object.kind == "abstract class"
    for member in node.members:
        member.object.kind.replace(" ", "_") == member.object.name
