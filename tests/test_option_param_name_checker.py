import ast
import textwrap

from flake8_click import ClickOptionFunctionArgumentChecker


def check_code(s: str):
    checker = ClickOptionFunctionArgumentChecker(tree=ast.parse(textwrap.dedent(s)))
    return list(checker.run())


def test_missing_option():
    l = check_code(
        """
          @cli.command()
          @click.option('-d', '--dummy')
          def build(foo): pass
        """
    )
    assert len(l) == 1


def test_multiple_missing_option():
    l = check_code(
        """
          @cli.command()
          @click.option('-d', '--dummy')
          @click.option('-f', '--fummy')
          def build(foo): pass
        """
    )
    print(l)
    assert len(l) == 1


def test_full_option():
    assert not check_code(
        """
          @cli.command()
          @click.option('-d', '--dummy')
          def build(dummy): pass
        """
    )
