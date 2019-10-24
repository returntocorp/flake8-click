import click


# should trigger CLC001
@click.command()
@click.option("-d")
def build():
    pass


# should trigger CLC100
@click.command()
@click.option("-d")
def build():
    pass
