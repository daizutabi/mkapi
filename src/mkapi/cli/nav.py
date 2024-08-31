import typer
from rich import print

app = typer.Typer(add_completion=False)


@app.command()
def list(module: str):
    from mkapi.cli.console import generate_nav_list

    list_ = generate_nav_list(module)
    print(list_)


@app.command()
def tree(module: str):
    from mkapi.cli.console import generate_nav_tree

    tree = generate_nav_tree(module)
    print(tree)
