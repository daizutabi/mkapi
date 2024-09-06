from __future__ import annotations

import sys
from pathlib import Path

from rich.tree import Tree

from mkapi.utils import is_package

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# from rich.console import Console
# from rich.table import Table


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

    if name.startswith("/") or not current:
        name = name[1:] if name.startswith("/") else name
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


def get_styled_name(fullname: str, *, exclude_prefix: int = 0) -> str | None:
    if not (name_module := get_name_module(fullname)):
        return None

    name, module = name_module
    if not module:
        styled_names = _get_styled_modules(name)

    else:
        styled_names = _get_styled_modules(module)
        name, *members = name.split(".")

        styled_names.extend(_get_styled_names(name, "green"))

        if members:
            styled_names.extend(_get_styled_names(members, "white"))

    if exclude_prefix:
        styled_names = styled_names[exclude_prefix:]

    return "[gray50].[/gray50]".join(styled_names)


def _get_styled_names(names: list[str] | str, color: str = "cyan") -> list[str]:
    if isinstance(names, str):
        names = names.split(".")

    return [f"[{color}]{name}[/{color}]" for name in names]


def _get_styled_modules(modules: list[str] | str) -> list[str]:
    if isinstance(modules, str):
        modules = modules.split(".")

    *packages, module = modules

    names = _get_styled_names(packages, "bold cyan") if packages else []
    color = "bold cyan" if is_package(".".join(modules)) else "cyan"
    names.extend(_get_styled_names(module, color))

    return names


def generate_nav_list(module: str, *, exclude_prefix: int = 0) -> list[str]:
    import mkapi.nav

    list_ = mkapi.nav.get_apinav(module, 1)
    it = (get_styled_name(item, exclude_prefix=exclude_prefix) for item in list_)
    return [name for name in it if name]


def generate_nav_tree(module: str) -> Tree | None:
    import mkapi.nav

    nav = mkapi.nav.get_apinav(module, 3)

    if not nav:
        return None

    name = get_styled_name(module)
    if not name:
        return None

    tree = Tree(name)

    if isinstance(nav[0], str):
        return tree
    else:
        _add_to_tree(tree, nav[0][module])

    return tree


def _add_to_tree(tree: Tree, data: list) -> None:
    for item in data:
        if isinstance(item, dict):
            for key, value in item.items():
                branch = tree.add(get_styled_name(key))  # type: ignore
                _add_to_tree(branch, value)
        else:
            tree.add(get_styled_name(item))  # type: ignore


# def crate_table(data: list[str], **kwargs) -> Table:
#     t = Table.grid(expand=True)
#     t.add_column(ratio=1)
#     t.add_row("foo " * 20, "bar " * 20)
#     print(t)
#     return

# console = Console()
# terminal_width = console.width
# item_width = 10
# columns = terminal_width // item_width
# table = Table(show_header=False, **kwargs)

# for _ in range(columns):
#     table.add_column("Item", justify="left")

# for i, item in enumerate(data):
#     if i % columns == 0:
#         table.add_row(*data[i : i + columns])

# return table
