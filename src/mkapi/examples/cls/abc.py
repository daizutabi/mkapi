from abc import ABC, abstractmethod


class AbstractMethodTypeExample(ABC):
    """Abstract class."""

    def method(self):
        """Method."""
        return self

    @classmethod
    def class_method(cls):
        """Class method."""
        return cls

    @staticmethod
    def static_method():
        """Static method."""
        return True

    @abstractmethod
    def abstract_method(self):
        """Abstract method."""

    @classmethod
    @abstractmethod
    def abstract_class_method(cls):
        """Abstract class method."""

    @staticmethod
    @abstractmethod
    def abstract_static_method():
        """Abstract static method."""

    @property
    @abstractmethod
    def abstract_read_only_property(self):
        """Abstract read only property."""

    @property
    @abstractmethod
    def abstract_read_write_property(self):
        """Abstract read write property."""

    @abstract_read_write_property.setter
    @abstractmethod
    def abstract_read_write_property(self, val):
        pass
