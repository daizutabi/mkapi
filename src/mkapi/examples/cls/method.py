class MethodTypeExample:
    """Example class."""

    def __init__(self, x: int):
        self._x = x

    def method(self, x):
        """Method."""

    def generator(self, x):
        """Generator."""
        yield x + 1

    @classmethod
    def class_method(cls, x):
        """Class method."""

    @staticmethod
    def static_method(x):
        """Static method."""

    @property
    def read_only_property(self):
        """Read only property."""
        return self._x

    @property
    def read_write_property(self):
        """Read write property."""
        return self._x

    @read_write_property.setter
    def read_write_property(self, x):
        self._x = x
