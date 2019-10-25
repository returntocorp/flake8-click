from flake8_click import ClickCommandArgumentAddTransformer
import libcst as cst

def main():
    fname = "tests/bad_examples.py"
    source_tree = cst.parse_module(open(fname).read())
    modified_tree = source_tree.visit(ClickCommandArgumentAddTransformer())
    print_diff(source_tree.code, modified_tree.code, fname)

def print_diff(tree1, tree2, filename):
    import difflib

    print(
        "".join(
            difflib.unified_diff(
                tree1.splitlines(1),
                tree2.splitlines(1),
                filename,
                filename,
                lineterm="\n",
            )
        )
    )

if __name__ == "__main__":
    main()