import typer
from rich import print

app = typer.Typer(add_completion=False)


@app.command()
def list(module: str):
    from mkapi.cli.console import generate_nav_list

    if list_ := generate_nav_list(module):
        print(list_)
    else:
        raise typer.Exit(1)


@app.command()
def tree(module: str):
    from mkapi.cli.console import generate_nav_tree

    if tree := generate_nav_tree(module):
        print(tree)
    else:
        raise typer.Exit(1)
