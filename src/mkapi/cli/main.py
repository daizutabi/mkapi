from __future__ import annotations

from typing import Annotated, Any

import typer
from rich import print
from rich.console import Console
from typer import Argument

from mkapi.cli.utils import (
    generate_nav_list,
    generate_nav_tree,
    get_fullname,
    get_name_module,
    get_package_name_from_current_dir,
    get_styled_name,
    is_package,
)

app = typer.Typer(add_completion=False)

console = Console()


@app.command(name="mkapi")
def cli(
    name: Annotated[
        str,
        Argument(
            show_default=False,
            help="The name of the object or module.",
        ),
    ] = "",
) -> None:
    repl(name)


def repl(name: str = "") -> None:
    if name and not get_fullname(name, ""):
        raise typer.Exit(1)

    current = name or get_package_name_from_current_dir() or ""

    while True:
        if current:
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

        if cmd in ("la", "ll", "ls"):
            ls(cmd, args, current)

        if cmd == "tree":
            tree(cmd, args, current)


def cd(args: list[str], current: str) -> str | None:
    from mkapi.cli.utils import get_fullname

    if not args:
        return get_package_name_from_current_dir()

    name = args[0]
    if fullname := get_fullname(name, current):
        return fullname

    error("cd", name)
    return None


def ls(cmd: str, args: list[str], current: str) -> None:
    from mkapi.nodes import parse_module

    if not args:
        if not current:
            return
        fullname = current
    elif not (fullname := get_fullname(args[0], current)):
        error(cmd, args[0])
        return

    if not (name_module := get_name_module(fullname)):
        error(cmd, fullname)
        return

    name, module = name_module

    # package
    if not module and is_package(name):
        if cmd in ("ls", "ll"):
            exclude_prefix = name.count(".") + 1
            if list_ := generate_nav_list(name, exclude_prefix=exclude_prefix):
                sep = "\n" if cmd == "ll" else " "
                print(sep.join(list_))
            return

        print(parse_module(name))
        return

    # module
    if not module:
        members = parse_module(name)
        if cmd == "ls":
            print(" ".join(name for name, _ in members))
            return

        for name, node in members:
            print(name, node)
        return

    print(name, module)


def tree(cmd: str, args: list[str], current: str) -> None:
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
        # package
        if tree := generate_nav_tree(name):
            print(tree)
            return

    print(name, module)


def error(cmd: str, name: str) -> None:
    print(f"[red]{cmd}: {name}: No such object or module[/red]")
