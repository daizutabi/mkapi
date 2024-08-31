import typer

from mkapi.cli import nav

app = typer.Typer(add_completion=False)
app.add_typer(nav.app, name="nav")
