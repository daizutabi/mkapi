import importlib
import sys

from mkapi.core import inspect
from mkapi.core.renderer import Renderer

if "examples" not in sys.path:
    sys.path.insert(0, "examples")

module = importlib.import_module("example.google")
module = importlib.reload(module)
module.function_with_types_in_docstring

import inspect
inspect.getmembers(module)
node = inspect.walk(module)

renderer = Renderer()

print(renderer.render(node))
