import ast
import textwrap
from typing import List

from flake8_click import ClickLaunchUsesLiteralChecker, ClickLaunchVisitor


def _visit(s: str) -> List[ast.Call]:
    visitor = ClickLaunchVisitor()
    visitor.visit(ast.parse(textwrap.dedent(s)))
    return visitor.unsafe_launch_sites


def _check(s: str) -> List[ast.Call]:
    checker = ClickLaunchUsesLiteralChecker(tree=ast.parse(textwrap.dedent(s)))
    return list(checker.run())


def test_literal_arg_launch():
    s = """
    import click
    click.launch("hi")
    """
    assert not _visit(s)


def test_literal_kw_launch():
    s = """
    import click
    click.launch(url="hi")
    """
    assert not _visit(s)


def test_input_arg_launch():
    s = """
    import click
    click.launch(x)
    """
    assert _visit(s)


def test_input_kw_launch():
    s = """
    import click
    click.launch(url=x)
    """
    assert _visit(s)


def test_launch_alias():
    s = """
    import click as c
    c.launch(x)
    """
    assert _visit(s)


def test_launch_alias_neg():
    s = """
    import click as c
    click.launch(x)
    """
    assert not _visit(s)


def test_launch_from():
    s = """
    from click import launch
    launch(x)
    """
    assert _visit(s)


def test_launch_from_alias():
    s = """
    from click import launch as cli_launch
    cli_launch(x)
    """
    assert _visit(s)


def test_launch_from_alias_neg():
    s = """
    from click import launch as cli_launch
    launch(x)
    """
    assert not _visit(s)


def test_check_no_results():
    s = """
    import click
    click.launch("static")
    """
    assert not _check(s)


def test_check_one_result():
    s = """
    import click
    click.launch(x)
    """
    assert len(_check(s)) == 1


def test_check_multiple_results():
    s = """
    import click
    click.launch(x)
    click.launch("b")
    click.launch(y)
    """
    assert len(_check(s)) == 2
