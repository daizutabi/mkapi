import inspect
import sys
from typing import Iterator,List,Any

import mkapi.core.node

if "examples" not in sys.path:
    sys.path.insert(0, "examples")

node = mkapi.core.node.get_node("example.google")
doc = node.members[5].members[1]
doc
