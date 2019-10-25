import ast
import textwrap

from flake8_click import ClickOptionFunctionArgumentChecker


def check_code(s: str):
    checker = ClickOptionFunctionArgumentChecker(tree=ast.parse(textwrap.dedent(s)))
    return list(checker.run())


def test_empty_args():
    s = """
    @click.command()
    @click.option()
    def run(y): pass
    """
    assert not check_code(s)


def test_no_string_args():
    s = """
    @click.command()
    @click.option(x)
    def run(y): pass
    """
    assert not check_code(s)


def test_missing_option():
    s = check_code(
        """
          @click.command()
          @click.option('-d', '--dummy')
          def build(foo): pass
        """
    )
    assert len(s) == 1


def test_multiple_missing_option():
    s = check_code(
        """
          @click.command()
          @click.option('-d', '--dummy')
          @click.option('-f', '--fummy')
          def build(foo): pass
        """
    )
    assert len(s) == 1


def test_full_option():
    assert not check_code(
        """
          @click.command()
          @click.option('-d', '--dummy')
          def build(dummy): pass
        """
    )
