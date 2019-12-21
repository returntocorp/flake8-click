import ast
import textwrap

from flake8_click.flake8_click import ClickOptionFunctionArgumentChecker, ClickOptionArgumentVisitor


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


def test_bool_option_with_slash():
    assert not check_code(
        """
          @click.option('--shout/--no-shout', default=False)
          def build(shout): pass
        """
    )


def test_expose_value_false():
    code = """
import click
@click.command("run", short_help="Run a development server.")
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option(
    "--cert", type=CertParamType(), help="Specify a certificate file to use HTTPS."
)
@click.option(
    "--key",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    callback=_validate_key,
    expose_value=False,
    help="The key file to use when specifying a certificate.",
)
@click.option(
    "--reload/--no-reload",
    default=None,
    help="Enable or disable the reloader. By default the reloader "
    "is active if debug is enabled.",
)
@click.option(
    "--debugger/--no-debugger",
    default=None,
    help="Enable or disable the debugger. By default the debugger "
    "is active if debug is enabled.",
)
@click.option(
    "--eager-loading/--lazy-loading",
    default=None,
    help="Enable or disable eager loading. By default eager "
    "loading is enabled if the reloader is disabled.",
)
@click.option(
    "--with-threads/--without-threads",
    default=True,
    help="Enable or disable multithreading.",
)
@click.option(
    "--extra-files",
    default=None,
    type=SeparatedPathType(),
    help=(
        "Extra files that trigger a reload on change. Multiple paths"
        " are separated by '{}'.".format(os.path.pathsep)
    ),
)
@pass_script_info
def run_command(
    info, host, port, reload, debugger, eager_loading, with_threads, cert, extra_files
):
    debug = get_debug_flag()
"""
    assert len(check_code(code)) == 0

def test_has_kwargs():
    code = """
import click
@main.command()
@click.option("--address", help="the seller/buyer address", type=str)
@click.option("--limit", help="default 50; max 1000.", type=int)
@click.option("--offset", help="start with 0; default 0.", type=int)
@click.option("--symbol", help="symbol", type=str)
@click.option(
    "--total",
    help="total number required, 0 for not required and 1 for required; default not required, return total=-1 in response",
    type=int,
)
def open_orders(hello=False, **kwargs):
    dex_run("get_open_orders", hello="world", **kwargs)
"""
    assert len(check_code(code)) == 0

def test_no_dash():
    code = """
from click import manager, argument, option
@manager.command()
@argument('email')
@argument('name')
@argument('inviter_email')
@option('--org', 'organization', default='default', help="The organization the user belongs to (leave blank for 'default')")
@option('--admin', 'is_admin', type=BOOL, default=False, help="set user as admin")
@option('--groups', 'groups', default=None, help="Comma seperated list of groups (leave blank for default).")
def invite(email, name, inviter_email, groups, is_admin=False,
           organization='default'):
    pass
"""
    assert len(check_code(code)) == 0

def test_no_dash_finding():
    code = """
from click import manager, argument, option
@manager.command()
@argument('email')
@argument('name')
@argument('inviter_email')
@option('--org', 'organization', default='default', help="The organization the user belongs to (leave blank for 'default')")
@option('--admin', 'is_admin', type=BOOL, default=False, help="set user as admin")
@option('--groups', 'groups', default=None, help="Comma seperated list of groups (leave blank for default).")
@option('--users', 'users')
def invite(email, name, inviter_email, groups, is_admin=False,
           organization='default'):
    pass
"""
    assert len(check_code(code)) == 1