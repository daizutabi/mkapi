"""Example subpackage for testing MkAPI."""

from .google import ExampleClass as ExampleClassGoogle
from .numpy import ExampleClass as ExampleClassNumPy

__all__ = ["ExampleClassGoogle", "ExampleClassNumPy"]
