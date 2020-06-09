from appendix.member_order_base import A


class B:
    def b(self):
        """mro index: 2, sourcefile index: 0, line number: 5."""


class C(A, B):
    def c(self):
        """mro index: 0, sourcefile index: 0, line number: 10."""
