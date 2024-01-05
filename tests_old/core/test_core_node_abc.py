from abc import ABC, abstractmethod

from mkapi.core.node import get_node
from mkapi.core.object import get_sourcefiles


class C(ABC):
    """Abstract class."""

    def method(self):  # noqa: B027
        """Method."""

    @classmethod  # noqa: B027
    def class_method(cls):
        """Classmethod."""

    @staticmethod  # noqa: B027
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


def test_get_module_sourcefiles():
    files = get_sourcefiles(C)
    assert len(files) == 1


def test_abc():
    node = get_node(C)
    assert node.object.kind == "abstract class"
    for member in node.members:
        obj = member.object
        assert obj.kind.replace(" ", "") == obj.name.replace("_", "")
