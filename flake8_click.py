import ast
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import attr

__version__ = "0.1.0"


class ClickMethodVisitor(ast.NodeVisitor):
    """
    Abstract visitor that visits click calls
    """

    def __init__(self):
        self.click_alias: str = "click"
        self.aliases: Dict[str, str] = {}

    def method_names(self) -> Set[str]:
        pass

    def visit_Import(self, node: ast.Import) -> None:
        """
        Visits:
            import click
            import click as alias
        """
        for n in node.names:
            if n.name == self.click_alias:
                self.click_alias = n.asname or n.name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        Visits:
            from click import ...
            from alias import ...
            from alias import ... as ...
        """
        if node.module == self.click_alias:
            for n in node.names:
                if n.name in self.method_names():
                    self.aliases[n.name] = n.asname or n.name

    def is_method(self, node: ast.Call, name: str):
        if isinstance(node.func, ast.Attribute):
            # click module imported
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == self.click_alias and node.func.attr == name:
                    return True
        elif isinstance(node.func, ast.Name) and name in self.aliases:
            # method imported from click
            if node.func.id == self.aliases[name]:
                return True
        return False

    def get_call_keywords(self, d: ast.Call) -> Dict[str, ast.Expr]:
        return dict((keyword.arg, keyword.value) for keyword in d.keywords)

    def get_func_arguments(self, f: ast.FunctionDef) -> List[str]:
        arg_names: List[str] = [arg.arg for arg in f.args.args]
        return arg_names


class ClickDecoratorVisitor(ClickMethodVisitor):
    METHOD_NAMES: Set[str] = {"option", "argument"}

    def __init__(self):
        self.option_definitions: List[ast.Call] = []
        super().__init__()

    def method_names(self) -> Set[str]:
        return ClickDecoratorVisitor.METHOD_NAMES.copy()

    def is_click_option(self, d: ast.Call):
        return self.is_method(d, "option")

    def is_click_argument(self, d: ast.Call):
        return self.is_method(d, "argument")

    def click_option_decorators(self, node: ast.FunctionDef) -> Iterator[ast.Call]:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            elif self.is_click_option(decorator):
                yield decorator

    def click_argument_decorators(self, node: ast.FunctionDef) -> Iterator[ast.Call]:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            elif self.is_click_argument(decorator):
                yield decorator


class ClickOptionHelpVisitor(ClickDecoratorVisitor):
    def visit_FunctionDef(self, f: ast.FunctionDef):
        """
        Visits each function checking for if its cli.command. If so,
        verifies the options have default and help text
        """
        for d in self.click_option_decorators(f):
            if not self.click_option_has_help_text(d):
                self.option_definitions.append(d)

    def click_option_has_help_text(self, d: ast.Call) -> bool:
        return "help" in self.get_call_keywords(d).keys()


class ClickOptionArgumentVisitor(ClickDecoratorVisitor):
    def __init__(self):
        self.func_def_to_option_call_def: Dict[ast.FunctionDef, List[str]] = {}
        super().__init__()

    def visit_FunctionDef(self, f: ast.FunctionDef):
        option_param_names: List[str] = []
        for d in self.click_option_decorators(f):
            param_name = self.get_option_param_name(d)
            if param_name is not None and not self.param_in_function_def(f, param_name):
                option_param_names.append(param_name)

        self.func_def_to_option_call_def[f] = option_param_names

    def param_in_function_def(self, f: ast.FunctionDef, param_name: str) -> bool:
        arg_names = self.get_func_arguments(f)
        return param_name in arg_names

    def get_option_param_name(self, d: ast.Call) -> Optional[str]:
        """
        Return the longest dash-prefixed argument based on
        Return param name based on https://click.palletsprojects.com/en/7.x/parameters/#parameter-names
        """
        args = list(a.s for a in d.args if isinstance(a, ast.Str))
        dash_prefixed_args = [arg.strip("-") for arg in args if arg[0] == "-"]
        non_dash_args = [arg for arg in args if arg[0] != "-"]

        def convert_kebab_to_snake(string) -> str:
            """ Converts kebab-case to snake_case """
            return string.replace("-", "_")

        if dash_prefixed_args:
            longest_arg = max(dash_prefixed_args, key=len)
            return convert_kebab_to_snake(longest_arg.lower())
        elif non_dash_args:
            return max(non_dash_args, key=len).lower()
        else:
            return None


class ClickLaunchVisitor(ClickMethodVisitor):
    """
    Finds unsafe usages of click.launch().

    click.launch() should not be called with user or environmental input, to avoid opening dangerous sites.

    Since the above is difficult, here we just look for non-literal calls.

    TODO: Add taint tracking
    """

    METHOD_NAMES = {"launch"}

    def __init__(self):
        self.unsafe_launch_sites: List[ast.Call] = []
        super().__init__()

    def method_names(self):
        return ClickLaunchVisitor.METHOD_NAMES

    def visit_Call(self, node: ast.Call) -> None:
        """
        Visits:
            click.launch(...)
            alias.launch(...)
            launch(...)
            launch_alias(...)
        as necessary
        """
        if self.is_method(node, "launch"):
            # validate launch argument is literal
            url_node = None
            kws = dict((k.arg, k.value) for k in node.keywords)

            if len(node.args) > 0:
                url_node = node.args[0]
            elif "url" in kws:
                url_node = kws["url"]

            if not isinstance(url_node, ast.Str):
                self.unsafe_launch_sites.append(node)


@attr.s
class ClickNamingVisitor(ClickDecoratorVisitor):
    malformed_options = attr.ib(
        type=List[Tuple[ast.AST, str]], default=attr.Factory(list)
    )
    malformed_arguments = attr.ib(
        type=List[Tuple[ast.AST, str]], default=attr.Factory(list)
    )
    missing_parameters = attr.ib(type=List[ast.AST], default=attr.Factory(list))

    def __attrs_post_init__(self):
        super().__init__()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for d in self.click_option_decorators(node):
            if d.args:
                name = d.args[0]
                if isinstance(name, ast.Str) and not name.s.startswith("-"):
                    self.malformed_options.append((node, name.s))
            else:
                self.missing_parameters.append(node)

        for d in self.click_argument_decorators(node):
            if d.args:
                name = d.args[0]
                if isinstance(name, ast.Str) and name.s.startswith("-"):
                    self.malformed_arguments.append((node, name.s))
            else:
                self.missing_parameters.append(node)


class ClickChecker:
    def run(self):
        pass

    def message_for(self, node: ast.AST, *args: Any) -> str:
        pass

    @staticmethod
    def get_name_call(node: ast.Call) -> str:
        return node.func.value.id

    @staticmethod
    def get_name_func(node: ast.FunctionDef) -> str:
        return node.name

    def response(self, node: ast.AST, *args: Any) -> Tuple[int, int, str, str]:
        return (
            node.lineno,
            node.col_offset,
            self.message_for(node, *args),
            str(type(self)),
        )


@attr.s
class ClickOptionHelpChecker(ClickChecker):
    name = "click-option-check"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        visitor = ClickOptionHelpVisitor()
        visitor.visit(self.tree)
        for call_def in visitor.option_definitions:
            yield self.response(call_def)

    def message_for(self, click_option: ast.Call, *args: Any):
        return f"CLC001 @click.option should have `help` text"


@attr.s
class ClickOptionFunctionArgumentChecker(ClickChecker):
    name = "click-option-function-argument-check"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        visitor = ClickOptionArgumentVisitor()
        visitor.visit(self.tree)
        func_def_to_option_call_def: Dict[
            ast.FunctionDef, List[str]
        ] = visitor.func_def_to_option_call_def
        for func_def, options in func_def_to_option_call_def.items():
            if len(options) > 0:
                yield self.response(func_def, options)

    def message_for(self, func_def: ast.FunctionDef, *args: Any):
        options = args[0]
        return f"CLC100: function `{self.get_name_func(func_def)}` missing parameter `{','.join(options)}` for `@click.option`"


@attr.s
class ClickLaunchUsesLiteralChecker(ClickChecker):
    name = "click-launch-uses-literal"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        visitor = ClickLaunchVisitor()
        visitor.visit(self.tree)
        for site in visitor.unsafe_launch_sites:
            yield self.response(site)

    def message_for(self, site: ast.Call, *args: Any):
        return f"CLC200: calls to click.launch() should use literal urls to prevent arbitrary site redirects"


@attr.s
class ClickNamingChecker(ClickChecker):
    name = "click-names-are-well-formed"
    version = __version__
    tree = attr.ib(type=ast.Module)
    BAD_OPTION = "option"
    BAD_ARGUMENT = "argument"
    MISSING = "missing"

    def run(self):
        visitor = ClickNamingVisitor()
        visitor.visit(self.tree)
        for node, option in visitor.malformed_options:
            yield self.response(node, option, self.BAD_OPTION)
        for node, argument in visitor.malformed_arguments:
            yield self.response(node, argument, self.BAD_ARGUMENT)
        for node in visitor.missing_parameters:
            yield self.response(node, "", self.MISSING)

    def message_for(self, node: ast.Call, *args: Any) -> str:
        name: str = args[0]
        tpe: str = args[1]
        if tpe == self.BAD_OPTION:
            return f"CLC101: option '{name}' should begin with a '-'"
        elif tpe == self.BAD_ARGUMENT:
            return f"CLC102: argument '{name}' should not begin with a '-'"
        elif tpe == self.MISSING:
            return f"CLC103: missing parameter name"


@attr.s
class ClickPracticeCheckers(object):
    CHECKER_TYPES = [ClickNamingChecker, ClickOptionFunctionArgumentChecker]
    name = "click-best-practices"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        checkers = [c(self.tree) for c in self.CHECKER_TYPES]
        return (r for c in checkers for r in c.run())
