import ast
import attr
from typing import List

__version__ = "0.1.0"


@attr.s
class ClickOptionChecker:
    name = "click-option-check"
    version = __version__
    tree = attr.ib(type=ast.Module)

    def run(self):
        visitor = ClickCommandVisitor()
        visitor.visit(self.tree)
        for call_def in visitor.option_definitions:
            yield (
                call_def.lineno,
                call_def.col_offset,
                self._message_for(call_def),
                "ClickOptionChecker",
            )

    def _message_for(self, click_option: ast.Call):
        return f"CLC001 @click.option should have `help` text"


@attr.s(auto_attribs=True)
class ClickCommandVisitor(ast.NodeVisitor):
    option_definitions: List[ast.Call] = attr.Factory(list)

    def visit_FunctionDef(self, f: ast.FunctionDef):
        """
        Visits each function checking for if its cli.command. If so,
        verifies the options have default and help text
        """
        use_cli_command = False
        option_has_default = False
        for decorator in f.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if self.is_click_command(decorator):
                use_cli_command = True
            elif self.is_click_option(decorator):
                if not use_cli_command:
                    continue
                if self.is_click_option_proper(decorator):
                    self.option_definitions.append(decorator)

    def is_click_command(self, d: ast.Call):
        return hasattr(d.func, "attr") and d.func.attr == "command"

    def is_click_option(self, d: ast.Call):
        return hasattr(d.func, "attr") and d.func.attr == "option"

    def is_click_option_proper(self, d: ast.Call) -> bool:
        keywords: List[str] = [keyword.arg for keyword in d.keywords]
        if not "help" in keywords:
            return True
        else:
            return False

