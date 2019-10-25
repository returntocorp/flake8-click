
import libcst as cst
import textwrap
from flake8_click import ClickCommandArgumentAddTransformer

def check_transform(source_py: str) -> str:
    source_tree = cst.parse_module(source_py)
    transformer = ClickCommandArgumentAddTransformer()
    modified_tree = source_tree.visit(transformer)

    c = modified_tree.code
    return c

def test_transform_simple():
    py = '''
@cli.command()
@click.option('-d', '--dummy')
def build(foo): pass
    '''
    expected = '''
@cli.command()
@click.option('-d', '--dummy')
def build(foo, dummy): pass
    '''
    assert check_transform(py) == expected