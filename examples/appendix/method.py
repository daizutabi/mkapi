class MethodTypeExample:
    """Example class."""

    def method(self, x):
        "Method."

    @classmethod
    def class_method(cls, x):
        "Class method."

    @staticmethod
    def static_method(x):
        "Static method."

    @property
    def read_only_property(x):
        "Read only property."

    @property
    def read_write_property(x):
        "Read write property."

    @read_write_property.setter
    def read_write_property(x):
        pass
