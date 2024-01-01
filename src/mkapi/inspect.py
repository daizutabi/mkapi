"""Inspect module."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Ref:
    """Reference of type."""

    fullname: str
