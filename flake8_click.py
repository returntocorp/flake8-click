import ast
from typing import Dict, List, Optional, Set

import attr

__version__ = "0.1.0"


@attr.s(auto_attribs=True)
class ClickMethodVisitor(ast.NodeVisitor):
    """
    Abstract visitor that visits `click.command`-s
    """

    METHOD_NAMES: Set[str] = {"command", "option"}

    option_definitions: List[ast.Call] = attr.Factory(list)
    click_alias: str = "click"
    aliases: Dict[str, str] = attr.Factory(dict)

    def method_names(self) -> Set[str]:
        return ClickMethodVisitor.METHOD_NAMES

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

    def is_click_command(self, d: ast.Call):
        return self.is_method(d, "command")

    def is_click_option(self, d: ast.Call):
        return self.is_method(d, "option")

    def get_call_keywords(self, d: ast.Call) -> Dict[str, ast.Expr]:
        return dict((keyword.arg, keyword.value) for keyword in d.keywords)

    def get_call_arguments(self, d: ast.Call) -> List[str]:
        args: List[str] = [arg.s for arg in d.args]
        return args

    def get_func_arguments(self, f: ast.FunctionDef) -> List[str]:
        arg_names: List[str] = [arg.arg for arg in f.args.args]
        return arg_names


class ClickOptionHelpVisitor(ClickMethodVisitor):
    def visit_FunctionDef(self, f: ast.FunctionDef):
        """
        Visits each function checking for if its cli.command. If so,
        verifies the options have default and help text
        """
        use_cli_command = False
        for decorator in f.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if self.is_click_command(decorator):
                use_cli_command = True
            elif self.is_click_option(decorator):
                if not use_cli_command:
                    continue
                if not self.click_option_has_help_text(decorator):
                    self.option_definitions.append(decorator)

    def click_option_has_help_text(self, d: ast.Call) -> bool:
        return "help" in self.get_call_keywords(d).keys()


@attr.s(auto_attribs=True)
class ClickOptionArgumentVisitor(ClickMethodVisitor):
    func_def_to_option_call_def: Dict[ast.FunctionDef, List[str]] = attr.Factory(dict)

    def visit_FunctionDef(self, f: ast.FunctionDef):
        option_param_names: List[str] = []
        use_cli_command = False
        for decorator in f.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if self.is_click_command(decorator):
                use_cli_command = True
            elif self.is_click_option(decorator):
                if not use_cli_command:
                    continue
                param_name = self.get_option_param_name(decorator)
                if not self.param_in_function_def(f, param_name):
                    option_param_names.append(param_name)

        self.func_def_to_option_call_def[f] = option_param_names

    def param_in_function_def(self, f: ast.FunctionDef, param_name: str) -> bool:
        arg_names = self.get_func_arguments(f)
        return param_name in arg_names

    def get_option_param_name(self, d: ast.Call) -> str:
        """
        Return the longest dash-prefixed argument based on
        Return param name based on https://click.palletsprojects.com/en/7.x/parameters/#parameter-names
        """
        args = self.get_call_arguments(d)
        dash_prefixed_args = [arg.strip("-") for arg in args if arg[0] == "-"]
        non_dash_args = [arg for arg in args if arg[0] != "-"]

        def convert_kebab_to_snake(string) -> str:
            """ Converts kebab-case to snake_case """
            return string.replace("-", "_")

        if len(non_dash_args) == 0:
            longest_arg = max(dash_prefixed_args, key=len)
            return convert_kebab_to_snake(longest_arg.lower())
        else:
            return max(non_dash_args, key=len).lower()


@attr.s
class ClickLaunchVisitor(ClickMethodVisitor):
    """
    Finds unsafe usages of click.launch().

    click.launch() should not be called with user or environmental input, to avoid opening dangerous sites.

    Since the above is difficult, here we just look for non-literal calls.

    TODO: Add taint tracking
    """

    METHOD_NAMES = {"launch"}
    unsafe_launch_sites = attr.ib(type=List[ast.Call], default=attr.Factory(list))

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
class ClickChoiceVisitor(object):
    dict_name = attr.ib(default=None, type=Optional[str])
    dict_context = attr.ib(default=None, type=Optional[str])

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Dict):
            self.dict_name = node.targets[0].id
            self.dict_context = node.targets[0].ctx


class ClickChecker:
    def run(self):
        pass

    def get_name_call(self, node: ast.Call) -> str:
        return node.func.value.id

    def get_name_func(self, node: ast.FunctionDef) -> str:
        return node.name


@attr.s
class ClickOptionHelpChecker(ClickChecker):
    name = "click-option-check"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        visitor = ClickOptionHelpVisitor()
        visitor.visit(self.tree)
        for call_def in visitor.option_definitions:
            yield (
                call_def.lineno,
                call_def.col_offset,
                self._message_for(call_def),
                "ClickOptionHelpChecker",
            )

    def _message_for(self, click_option: ast.Call):
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
                yield (
                    func_def.lineno,
                    func_def.col_offset,
                    self._message_for(func_def, options),
                    "ClickOptionFunctionArgumentChecker",
                )

    def _message_for(self, func_def: ast.FunctionDef, options: List[str]):
        return f"CLC100: function `{self.get_name_func(func_def)}` missing parameter `{','.join(options)}` for `@click.option`{'-s' if len(options) > 0 else ''}"


@attr.s
class ClickLaunchUsesLiteralChecker(object):
    name = "click-launch-uses-literal"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        visitor = ClickLaunchVisitor()
        visitor.visit(self.tree)
        for site in visitor.unsafe_launch_sites:
            yield (
                site.lineno,
                site.col_offset,
                self._message_for(site),
                "ClickLaunchUsesLiteralChecker",
            )

    def _message_for(self, site: ast.Call):
        return f"CLC200: calls to click.launch() should use literal urls to prevent arbitrary site redirects"
