from __future__ import annotations

from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File

from mkapi.utils import get_module_path


def generate_file(config: MkDocsConfig, src_uri: str, name: str) -> File:
    file = File.generated(config, src_uri, content=name)

    def is_modified() -> bool:
        dest_path = Path(file.abs_dest_path)
        if not dest_path.exists():
            return True

        if not (module_path := get_module_path(name)):
            return True

        return dest_path.stat().st_mtime < module_path.stat().st_mtime

    file.is_modified = is_modified
    return file
