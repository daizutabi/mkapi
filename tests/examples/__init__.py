"""Example package for testing MkAPI."""

from examples import styles
from examples.subpackage import module as M
from examples.subpackage.module import A

__all__ = ["styles", "M", "A"]
