class A:
    """Class"""

    def m(self, x):
        "Method"

    @classmethod
    def c(cls, x):
        "Class method"

    @staticmethod
    def s(x):
        "Static method"

    @property
    def r(x):
        "Read only property"

    @property
    def w(x):
        "Read write property"

    @w.setter
    def w(x):
        pass
