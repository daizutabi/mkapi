from __future__ import annotations

import abc


class Foo(abc.ABC):
    def __init__(self):
        """Constructor"""
        pass

    @abc.abstractmethod
    def blubb(self, x):
        raise NotImplementedError


class Bar(abc.ABC):

    _x: int = 0

    def __init__(self):
        # """ sdhsehes """
        x = 0

    def blubb(self, x):
        """ blubb """
        self._x = x

    def __call__(self, x):
        """ pls call me :-) """
        return self.blubb(x)
