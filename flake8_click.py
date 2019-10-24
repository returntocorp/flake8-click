import ast
import attr
import re
from typing import List, Dict

__version__ = "0.1.0"




@attr.s(auto_attribs=True)
class ClickCommandVisitor(ast.NodeVisitor):
    """
    Abstract visitor that visits `click.command`-s
    """
    option_definitions: List[ast.Call] = attr.Factory(list)

    def visit_FunctionDef(self, f: ast.FunctionDef):
        """ Abstract Visiter-specific logic to be implemented by inheriters """
        pass

    def is_click_command(self, d: ast.Call):
        return hasattr(d.func, "attr") and d.func.attr == "command"

    def is_click_option(self, d: ast.Call):
        return hasattr(d.func, "attr") and d.func.attr == "option"

    def get_call_keywords(self, d: ast.Call)-> List[str]:
        keywords: List[str] = [keyword.arg for keyword in d.keywords]
        return keywords

    def get_call_arguments(self, d: ast.Call)-> List[str]:
        args: List[str] = [arg.s for arg in d.args]
        return args

    def get_func_arguments(self, f: ast.FunctionDef)-> List[str]:
        arg_names: List[str] = [arg.arg for arg in f.args.args]
        return arg_names

class ClickOptionHelpVisitor(ClickCommandVisitor):
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
        return "help" in self.get_call_keywords(d)


@attr.s(auto_attribs=True)
class ClickOptionArgumentVisitor(ClickCommandVisitor):
    func_def_to_option_call_def: Dict[ast.FunctionDef, List[str]] = attr.Factory(dict)

    def visit_FunctionDef(self, f: ast.FunctionDef):
        option_param_names: List[str] = []
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
        dash_prefixed_args = [arg.strip("-") for arg in args if arg[0] == '-']
        non_dash_args = [arg for arg in args if arg[0] != '-']

        def convert_kebab_to_snake(string) -> str:
            """ Converts kebab-case to snake_case """
            return string.replace("-", "_")

        if len(non_dash_args) == 0:
            longest_arg = max(dash_prefixed_args, key=len)
            return convert_kebab_to_snake(longest_arg.lower())
        else:
            return max(non_dash_args, key=len).lower()

class ClickChecker:
    def run(self):
        pass

    def get_name_call(self, node: ast.Call)->str:
        return node.func.value.id

    def get_name_func(self, node: ast.FunctionDef)->str:
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
        func_def_to_option_call_def: Dict[ast.FunctionDef, List[str]] = visitor.func_def_to_option_call_def
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
