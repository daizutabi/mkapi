import typer
from rich import print

app = typer.Typer()


@app.command()
def page():
    print("aa")
