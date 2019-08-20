import ast
from click_best_practices import ClickBestPracticeChecker
import textwrap


def check_code(s: str):
    checker = ClickBestPracticeChecker(tree=ast.parse(textwrap.dedent(s)))
    return list(checker.run())


def test_empty_option():
    assert (
        len(
            check_code(
                """
              @cli.command()
              @click.option('-d')
              def build(): pass
            """
            )
        )
        == 1
    )


def test_full_option():
    assert not check_code(
        """
          @cli.command()
          @click.option('-d', help='dummy', default='dummy')
          def build(): pass
        """
    )


def test_absenceof_either_argument():
    assert (
        len(
            check_code(
                """
          @cli.command()
          @click.option('-d', default='dummy')
          def build(): pass
        """
            )
        )
        == 1
    )
    assert not check_code(
        """
          @cli.command()
          @click.option('-d', help='dummy')
          def build(): pass
        """
    )
