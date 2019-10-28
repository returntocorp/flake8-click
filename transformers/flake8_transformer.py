import attr
import libcst as cst
import ast

from typing import Union, Dict, List, Optional

@attr.s(auto_attribs=True)
class ClickCommandArgumentAddTransformer(cst.CSTTransformer):
    func_def_to_option_call_def: Dict[str, List[str]] = attr.Factory(dict)

    def is_click_command(self, d: Union[ast.Call, cst.Call]):
        if isinstance(d, ast.Call):
            return hasattr(d.func, "attr") and d.func.attr == "command"
        else:
            return hasattr(d.func, "attr") and d.func.attr.value == "command"

    def is_click_option(self, d: Union[ast.Call, cst.Call]):
        if isinstance(d, ast.Call):
            return hasattr(d.func, "attr") and d.func.attr == "option"
        else:
            return hasattr(d.func, "attr") and d.func.attr.value == "option"

    def visit_FunctionDef(self, f: cst.FunctionDef) -> Optional[bool]:
        option_param_names: List[str] = []
        for decorator in f.decorators:
            decorator = decorator.decorator
            if not isinstance(decorator, cst.Call):
                continue
            if self.is_click_command(decorator):
                use_cli_command = True
            elif self.is_click_option(decorator):
                if not use_cli_command:
                    continue
                param_name = self.get_option_param_name(decorator)
                if not self.param_in_function_def(f, param_name):
                    option_param_names.append(param_name)

        if option_param_names:
            self.func_def_to_option_call_def[self.get_name_func(f)] = option_param_names
            return True
        else:
            return False

    def param_in_function_def(self, f: Union[ast.FunctionDef, cst.FunctionDef], param_name: str) -> bool:
        arg_names = self.get_func_arguments(f)
        return param_name in arg_names

    def get_call_arguments(self, d: Union[ast.Call, cst.Call])-> List[str]:
        args: List[str] = [ast.literal_eval(arg.value.value) if isinstance(arg, cst.Arg) else arg.s for arg in d.args]
        return args

    def get_func_arguments(self, f: Union[ast.FunctionDef, cst.FunctionDef])-> List[str]:
        arg_names: List[str] = []
        if isinstance(f, ast.FunctionDef):
            arg_names = [arg.arg for arg in f.args.args]
        else:
            arg_names = [param.name.value for param in f.params.params]
        return arg_names

    def get_option_param_name(self, d: Union[ast.Call, cst.Call]) -> str:
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

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        updated_params: List[Tuple[cst.Param, Optional[cst.Annotation]]] = list(updated_node.params.params)
        func_name = self.get_name_func(original_node)
        param_names_to_add: List[Tuple[cst.Param, Optional[cst.Annotation]]] = [
            cst.Param(name=cst.Name(name))
            for name in
            self.func_def_to_option_call_def.get(func_name, [])
        ]
        updated_params += param_names_to_add
        return updated_node.with_changes(
            params=cst.Parameters(params=tuple(updated_params))
        )

    def get_name_func(self, node: Union[ast.FunctionDef, cst.FunctionDef]) -> str:
        return node.name.value