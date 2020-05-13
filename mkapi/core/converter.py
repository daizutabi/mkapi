import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List

from mkapi.core import inspect
from mkapi.core.page import Page
from mkapi.core.renderer import Renderer

PATTERN = re.compile(r"^\[mkapi\]\((.*?)\)$", re.MULTILINE)


@dataclass
class Converter:
    pages: Dict[str, Page] = field(default_factory=dict)
    renderer: Renderer = Renderer()
    dirty: bool = False

    def convert(self, path: str) -> str:
        """Convert a source file if needed.

        Args:
            path: the source path to be converted.

        Returns:
            Converted output text.
        """
        if not self.dirty:
            self.pages.clear()
        elif path in self.pages:
            if self.pages[path].st_mtime == os.stat(path).st_mtime:
                return self.pages[path].source
            else:
                self.pages.pop(path)

        if path not in self.pages:
            self.pages[path] = Page(path)
            self.pages[path].read()

        page = self.pages[path]
        page.source = "\n\n".join(self.render(page.source))
        page.st_mtime = os.stat(path).st_mtime
        return page.source

    def convert_from_files(self, paths: Iterable[str]) -> List[str]:
        """Convert entire pages

        Args:
            paths: path list for pages

        Returns:
            List of converted pages.
        """
        for path in paths:
            self.convert(path)
        return [self.pages[path].source for path in paths]

    def render(self, source: str) -> Iterator[str]:
        cursor = 0
        for match in PATTERN.finditer(source):
            start, end = match.start(), match.end()
            if cursor < start:
                yield source[cursor:start]
            name = match.group(1)
            node = inspect.get_node(name)
            yield self.renderer.render(node)
            cursor = end
        if cursor < len(source):
            yield source[cursor:]
