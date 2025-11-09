"""Test generation module using AST analysis."""

import ast
from typing import Any, Dict, List


class TestGenerator:
    """Intelligent pytest test generator using AST analysis."""
    
    @staticmethod
    def analyze_function(node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a function to understand its behavior."""
        info = {
            "name": node.name,
            "args": [],
            "returns": None,
            "docstring": ast.get_docstring(node),
            "raises": [],
            "calls": []
        }
        
        # Analyze arguments
        for arg in node.args.args:
            arg_info = {"name": arg.arg, "annotation": None}
            if arg.annotation:
                arg_info["annotation"] = ast.unparse(arg.annotation)
            info["args"].append(arg_info)
        
        # Analyze return type
        if node.returns:
            info["returns"] = ast.unparse(node.returns)
        
        # Find raise statements
        class RaiseVisitor(ast.NodeVisitor):
            def visit_Raise(self, node):
                if node.exc:
                    exc_type = ast.unparse(node.exc).split('(')[0]
                    info["raises"].append(exc_type)
        
        RaiseVisitor().visit(node)
        
        return info
    
    @staticmethod
    def generate_test_cases(func_info: Dict[str, Any]) -> List[str]:
        """Generate multiple test cases for a function."""
        tests = []
        name = func_info["name"]
        args = func_info["args"]
        
        # Test 1: Happy path with valid inputs
        test_args = []
        for arg in args:
            arg_name = arg["name"]
            annotation = arg.get("annotation") or ""
            annotation_lower = annotation.lower() if annotation else ""
            
            # Generate appropriate test values based on type hints or names
            if "int" in annotation_lower or "num" in arg_name.lower():
                test_args.append("1")
            elif "str" in annotation_lower or "name" in arg_name.lower() or "text" in arg_name.lower():
                test_args.append('"test_string"')
            elif "bool" in annotation_lower or arg_name.startswith("is_") or arg_name.startswith("has_"):
                test_args.append("True")
            elif "list" in annotation_lower:
                test_args.append("[1, 2, 3]")
            elif "dict" in annotation_lower:
                test_args.append('{"key": "value"}')
            elif "path" in arg_name.lower() or "file" in arg_name.lower():
                test_args.append('"/tmp/test_file"')
            else:
                test_args.append("None")
        
        args_str = ", ".join(test_args)
        
        tests.append(f"""
def test_{name}_basic():
    \"\"\"Test {name} with basic valid inputs.\"\"\"
    result = {name}({args_str})
    assert result is not None
""")
        
        # Test 2: Edge cases
        if any("int" in (arg.get("annotation") or "").lower() for arg in args):
            edge_args = []
            for arg in args:
                if "int" in (arg.get("annotation") or "").lower():
                    edge_args.append("0")
                else:
                    edge_args.append(test_args[args.index(arg)])
            edge_str = ", ".join(edge_args)
            tests.append(f"""
def test_{name}_edge_case_zero():
    \"\"\"Test {name} with edge case: zero values.\"\"\"
    result = {name}({edge_str})
    assert result is not None
""")
        
        # Test 3: Exception handling
        if func_info["raises"]:
            for exc in func_info["raises"]:
                tests.append(f"""
def test_{name}_raises_{exc.lower()}():
    \"\"\"Test {name} raises {exc} appropriately.\"\"\"
    with pytest.raises({exc}):
        {name}(invalid_input)
""")
        
        # Test 4: Type validation (if type hints present)
        if any(arg.get("annotation") for arg in args):
            tests.append(f"""
def test_{name}_type_validation():
    \"\"\"Test {name} with incorrect types.\"\"\"
    with pytest.raises((TypeError, ValueError, AttributeError)):
        {name}("wrong_type" if not any("str" in (arg.get("annotation") or "").lower() for arg in {args}) else 123)
""")
        
        return tests
    
    @staticmethod
    def generate_tests(code: str, module_name: str = "module") -> str:
        """Generate comprehensive pytest tests from source code."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"# Syntax error in source code: {e}\n"
        
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        
        test_code = [
            "import pytest",
            f"from {module_name} import *",
            "",
            "# Auto-generated tests by NeuroDev MCP",
            "# Review and customize as needed",
            ""
        ]
        
        # Generate tests for standalone functions
        for func in functions:
            func_info = TestGenerator.analyze_function(func)
            test_cases = TestGenerator.generate_test_cases(func_info)
            test_code.extend(test_cases)
        
        # Generate tests for class methods
        for cls in classes:
            cls_name = cls.name
            test_code.append(f"\n\nclass Test{cls_name}:")
            test_code.append(f'    """Tests for {cls_name} class."""')
            
            methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
            for method in methods:
                func_info = TestGenerator.analyze_function(method)
                test_cases = TestGenerator.generate_test_cases(func_info)
                # Indent for class
                test_code.extend(["    " + line if line.strip() else line for tc in test_cases for line in tc.split('\n')])
        
        return "\n".join(test_code)
