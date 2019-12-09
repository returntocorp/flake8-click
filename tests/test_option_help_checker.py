import ast
import textwrap

from flake8_click.flake8_click import ClickOptionHelpChecker


def check_code(s: str):
    checker = ClickOptionHelpChecker(tree=ast.parse(textwrap.dedent(s)))
    return list(checker.run())


def test_empty_option():
    s = """
      @click.command()
      @click.option('-d')
      def build(): pass
    """
    assert len(check_code(s)) == 1


def test_full_option():
    assert not check_code(
        """
          @click.command()
          @click.option('-d', help='dummy', default='dummy')
          def build(): pass
        """
    )


def test_absenceof_either_argument():
    s = """
      @click.command()
      @click.option('-d', default='dummy')
      def build(): pass
    """
    assert len(check_code(s)) == 1

    assert not check_code(
        """
          @cli.command()
          @click.option('-d', help='dummy')
          def build(): pass
        """
    )
