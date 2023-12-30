"""Node module."""
from __future__ import annotations

import ast
import importlib
import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType

# @dataclass
# class AST
