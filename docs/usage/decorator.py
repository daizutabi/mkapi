"""md
# Working with Decorator

{{ # cache:clear }}
"""

import mkapi

# ## Basics


class A:
    """A class"""

    def m(self, x):
        "A method"

    @classmethod
    def c(cls, x):
        "A classmethod"

    @staticmethod
    def s(x):
        "A staticmethod"

    @property
    def r(x):
        "A read only property"

    @property
    def w(x):
        "A read write property"

    @w.setter
    def w(x):
        pass


mkapi.display(A)
# -
mkapi.display(Foo)
# -
mkapi.display(Bar)
