import io
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Page:
    path: str
    source: str = field(default="", init=False)
    st_mtime: float = field(default=0.0, init=False)
    meta: Dict[str, Any] = field(default_factory=dict, init=False)

    def read(self) -> str:
        with io.open(self.path, "r", encoding="utf-8-sig", errors="strict") as f:
            self.source = f.read()
        return self.source
