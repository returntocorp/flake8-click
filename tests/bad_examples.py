import click


# should trigger CLC001
@click.command()
@click.option("-d")
def build(d):
    pass


# should trigger CLC100
@click.command()
@click.option("-d", help="Hi mom")
def build():
    pass


# should trigger CLC200
def bad_launch(x: str) -> None:
    click.launch(x)
