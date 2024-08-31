import typer

from mkapi.cli import nav, page

app = typer.Typer()
app.add_typer(nav.app, name="nav")
app.add_typer(page.app, name="page")
