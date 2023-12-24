class A(type):
    """A"""

    def f(cls):
        """f"""


class B(A):
    """B"""

    def g(self, x):
        """g

        Args:
            x (int): parameter.
        """


class C(B):
    """C"""

    def g(self, x):
        pass


class D:
    """D"""


class E(D):
    """E"""


class F(E):
    """F"""
