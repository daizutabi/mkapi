from __future__ import annotations

import sys
from pathlib import Path

from rich.tree import Tree

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def find_pyproject_toml(start_dir: Path | str | None = None) -> Path | None:
    """Return the first `pyproject.toml` found by traversing up from the current directory.

    This function searches for the `pyproject.toml` file starting from the specified
    directory and moving up to its parent directories. If the file is found, its path
    is returned; otherwise, None is returned.

    Args:
        start_dir (Path): The directory to start the search from. If not specified,
                           the current working directory is used.

    Returns:
        Path | None: The path to the first found `pyproject.toml`, or None if not found.
    """
    if start_dir is None:
        start_dir = Path.cwd()
    elif isinstance(start_dir, str):
        start_dir = Path(start_dir)

    current_dir = start_dir

    while current_dir != current_dir.parent:  # Until reaching the root directory
        pyproject_path = current_dir / "pyproject.toml"

        if pyproject_path.is_file():
            return pyproject_path

        current_dir = current_dir.parent

    return None


def get_package_name(path: Path) -> str | None:
    """Retrieve the package name from the specified `pyproject.toml` file.

    This function reads the `pyproject.toml` file and extracts the package name
    defined under the `[project]` or `[tool.poetry]` section. If the package name
    is not found, None is returned.

    Args:
        path (Path): The path to the `pyproject.toml` file.

    Returns:
        str | None: The package name if found, or None if not found.
    """
    try:
        with path.open("rb") as f:
            toml = tomllib.load(f)

        if name := toml.get("project", {}).get("name"):
            return name

        if name := toml.get("tool", {}).get("poetry", {}).get("name"):
            return name

        return None

    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return None


def get_package_name_from_current_dir() -> str | None:
    """Retrieve the package name from the `pyproject.toml` file in the current directory.

    This function searches for the `pyproject.toml` file in the current
    directory and extracts the package name defined under the `[project]` or
    `[tool.poetry]` section. If the package name is not found, None is returned.

    Returns:
        str | None: The package name if found, or None if not found.
    """
    if pyproject_path := find_pyproject_toml():
        return get_package_name(pyproject_path)

    return None


def get_fullname(name: str, current: str) -> str | None:
    from mkapi.nodes import get_fullname

    if name == ".":
        return current

    if name == "..":
        if "." in current:
            return current.rsplit(".", 1)[0]
        else:
            return None

    if name.startswith("/"):
        name = name[1:]
        if fullname := get_fullname(name):
            return fullname

        return None

    if fullname := get_fullname(f"{current}.{name}"):
        return fullname

    if fullname := get_fullname(name):
        return fullname

    return None


def get_name_module(name: str) -> tuple[str, str | None] | None:
    from mkapi.nodes import get_fullname, split_module_name

    fullname = get_fullname(name)
    if not fullname:
        return None

    return split_module_name(fullname)


def get_styled_name(fullname: str) -> str | None:
    if not (name_module := get_name_module(fullname)):
        return None

    name, module = name_module
    if not module:
        return _get_styled_name(name, "bold cyan")

    module = _get_styled_name(module, "bold cyan")
    name, *members = name.split(".")

    member = _get_styled_name(members, "bold white")
    name = _get_styled_name(name, "bold green")

    return f"{module}[gray].[/gray]{name}[gray].[/gray]{member}"


def _get_styled_name(names: list[str] | str, color: str = "cyan") -> str:
    if isinstance(names, str):
        names = names.split(".")

    it = (f"[{color}]{name}[/{color}]" for name in names)
    print(names)
    return "[grey].[/grey]".join(it)


def generate_nav_list(module: str) -> list[str]:
    import mkapi.nav

    return mkapi.nav.get_apinav(module, 1)


def generate_nav_tree(module: str, color: str = "green") -> Tree | None:
    import mkapi.nav

    nav = mkapi.nav.get_apinav(module, 3)

    if not nav:
        return None

    tree = Tree(f"[{color}]{module}[/{color}]")

    if isinstance(nav[0], str):
        return tree
    else:
        _add_to_tree(tree, nav[0][module])

    return tree


def _add_to_tree(tree: Tree, data: list, color: str = "green") -> None:
    for item in data:
        if isinstance(item, dict):
            for key, value in item.items():
                branch = tree.add(f"[{color}]{key}[/{color}]")
                _add_to_tree(branch, value, color)
        else:
            tree.add(item)
