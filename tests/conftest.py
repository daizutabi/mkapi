import importlib
import sys
from pathlib import Path

path = str(Path(__file__).parent)
if path not in sys.path:
    sys.path.insert(0, str(path))

assert importlib.import_module("example")
