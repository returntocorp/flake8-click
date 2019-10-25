import click


# should trigger CLC001
@click.command()
@click.option("-d")
def bad_help(d):
    pass


# should trigger CLC100
@click.command()
@click.option("-d", help="Hi mom")
def bad_option():
    pass


# should trigger CLC200
def bad_launch(x: str) -> None:
    click.launch(x)
