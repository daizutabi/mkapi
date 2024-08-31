from __future__ import annotations

from rich.tree import Tree

import mkapi.nav


def generate_nav_list(module: str) -> str:
    nav = mkapi.nav.get_apinav(module, 2)
    return "\n".join(nav)


def generate_nav_tree(module: str, color: str = "green") -> Tree | None:
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
