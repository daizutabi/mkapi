import typer

app = typer.Typer(add_completion=False)


@app.command()
def nav():
    import mkapi.nav

    def log(*args):
        print(*args)
        return []

    print(mkapi.nav.get_apinav("mkdocs.**"))


@app.command()
def cxli():
    print("Hello, World!")
