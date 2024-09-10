"""
Provide functions to generate files for MkDocs.
Specifically, it creates a `File` instance representing a generated file
based on the specified source URI and name.
The `is_modified` method of the generated `File` instance is set to check
if the destination file exists and if it is older than the module path.
This is used to determine if the file needs to be rebuilt in dirty mode.
"""

from __future__ import annotations

from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File

from mkapi.utils import get_module_path


def generate_file(config: MkDocsConfig, src_uri: str, name: str) -> File:
    """Generate a `File` instance for a given source URI and name.

    Create a `File` instance representing a generated file with the specified
    source URI and content. The `is_modified` method is set to check if the
    destination file exists and if it is older than the module path.

    Args:
        config (MkDocsConfig): The MkDocs configuration object.
        src_uri (str): The source URI of the file.
        name (str): The object name corresponding to the `src_uri`.

    Returns:
        File: A `File` instance representing the generated file.
    """
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
