from __future__ import annotations

from typing import Annotated, Any

import typer
from rich import print
from rich.console import Console
from rich.tree import Tree
from typer import Argument

from mkapi.cli.utils import (
    generate_nav_list,
    get_fullname,
    get_name_module,
    get_package_name_from_current_dir,
    get_styled_name,
)

app = typer.Typer(add_completion=False)

console = Console()


@app.command(name="mkapi")
def cli(
    name: Annotated[
        str,
        Argument(
            show_default=False,
            help="The name of the object or module to find.",
        ),
    ] = "",
):
    if not name:
        return repl()

    if result := parse(name):
        print(result)
        return
    else:
        raise typer.Exit(1)

    # if name.endswith("/"):
    #     if tree := get_tree(name[:-1]):
    #         print(tree)
    #     else:
    #         raise typer.Exit(1)

    # fullname = get_fullname(name)
    # if not fullname:
    #     raise typer.Exit(code=1)

    # print(fullname)
    # name_module = split_module_name(fullname)

    # if not name_module:
    #     raise typer.Exit(code=1)

    # name, module = name_module

    # if module:
    #     raise typer.Exit(code=1)

    # print(name)
    # node = get_module_node(name)
    # print(node)

    # nodes = parse(node, name)
    # print(nodes)


def parse(name: str) -> Any:
    from mkapi.nodes import get_fullname, parse
    from mkapi.utils import get_module_node, split_module_name

    if name == "exit":
        raise typer.Exit()

    if name.endswith("/"):
        return get_tree(name[:-1])

    return None


def repl():
    current = get_package_name_from_current_dir() or ""

    while True:
        print(get_styled_name(current), end="")
        print("> ", end="")
        args = input("")

        if not args:
            continue

        if args == "exit":
            raise typer.Exit()

        cmd, *args = args.split()

        if cmd == "cd" and (result := cd(args, current)):
            current = result

        if cmd in ("ls", "ll"):
            ls(cmd, args, current)


def ls(cmd: str, args: list[str], current: str) -> None:
    if not args:
        fullname = current
    elif not (fullname := get_fullname(args[0], current)):
        error(cmd, args[0])
        return

    if not (name_module := get_name_module(fullname)):
        error(cmd, fullname)
        return

    name, module = name_module
    if not module:
        if list_ := generate_nav_list(name, exclude_module=cmd == "ls"):
            print(list_)

    # list_ = [item.replace(f"{module}.", "") for item in list_[1:]]
    # if not fullname:
    #     raise typer.Exit(code=1)
    # if tree := generate_nav_list(current):
    #     print(tree)


def cd(args: list[str], current: str) -> str | None:
    from mkapi.cli.utils import get_fullname

    if not args:
        return get_package_name_from_current_dir()

    name = args[0]
    if fullname := get_fullname(name, current):
        return fullname

    error("cd", name)
    return None


def get_tree(module: str) -> Tree | None:
    from mkapi.cli.utils import generate_nav_tree

    if tree := generate_nav_tree(module):
        return tree

    return None


def error(cmd: str, name: str) -> None:
    print(f"[red]{cmd}: {name}: No such object or module[/red]")
