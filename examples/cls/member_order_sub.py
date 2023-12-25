from examples.cls.member_order_base import A


class B:
    def b(self):
        """Mro index: 2, sourcefile index: 0, line number: 5."""


class C(A, B):
    def c(self):
        """Mro index: 0, sourcefile index: 0, line number: 10."""
