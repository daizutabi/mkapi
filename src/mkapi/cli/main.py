from typing import Annotated

import typer
from typer import Argument

# from mkapi.cli import nav, page

app = typer.Typer(add_completion=False)
# app.add_typer(nav.app, name="nav")
# app.add_typer(page.app, name="page")


@app.command(name="mkapi")
def cli(
    obj: Annotated[
        str,
        Argument(
            metavar="OBJECT",
            show_default=False,
            help="Object to inspect",
        ),
    ],
):
    from mkapi.objects import get_object

    print(get_object(obj))
