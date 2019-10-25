import ast
import textwrap
from typing import List

from flake8_click import ClickNamingChecker


def _check(s: str) -> List[ast.Call]:
    checker = ClickNamingChecker(tree=ast.parse(textwrap.dedent(s)))
    return list(checker.run())


def test_correct_option():
    s = """
    @click.command
    @click.option("--bar")
    def foo(bar): pass
    """
    assert not _check(s)


def test_bad_option():
    s = """
    @click.command
    @click.option("bar")
    def foo(bar): pass
    """
    assert len(_check(s)) == 1


def test_correct_argument():
    s = """
    @click.command
    @click.argument("bar")
    def foo(bar): pass
    """
    assert not _check(s)


def test_bad_argument():
    s = """
    @click.command
    @click.argument("--bar")
    def foo(bar): pass
    """
    assert len(_check(s)) == 1


def test_missing_name():
    s = """
    @click.command
    @click.argument()
    def foo(): pass
    """
    assert len(_check(s)) == 1
