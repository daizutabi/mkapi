import inspect
import sys
from typing import Iterator,List,Any

import mkapi.core.inspect

if "examples" not in sys.path:
    sys.path.insert(0, "examples")

node = mkapi.core.inspect.get_node("example.google")
doc = node.members[3].docstring
