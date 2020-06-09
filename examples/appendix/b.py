from appendix.a import A  # mro_index: 0


class B:
    def b(self):  # lineno: 5
        """b"""


class C(A, B):
    def c(self):  # lineno: 10
        """c"""
