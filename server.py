#!/usr/bin/env python3
"""
NeuroDev MCP Server - Code Review, Test Generation, and Test Execution
Built with the official Model Context Protocol SDK

This MCP server provides powerful tools for Python development:
- Code Review: Multi-analyzer static analysis (pylint, flake8, mypy, bandit, radon)
- Test Generation: Intelligent pytest test generation using AST analysis
- Test Execution: Comprehensive test running with coverage reports
- Code Formatting: Auto-formatting with black and autopep8

Usage:
    python server.py

Or configure in your MCP client (e.g., Claude Desktop):
    {
      "mcpServers": {
        "neurodev-mcp": {
          "command": "python",
          "args": ["/path/to/server.py"]
        }
      }
    }
"""

import ast
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Initialize MCP server
app = Server("neurodev-mcp")


######################### Code Analysis Tools #########################


class CodeAnalyzer:
    """Multi-tool code analyzer combining various static analysis tools."""
    
    @staticmethod
    async def run_pylint(code: str, temp_file: str) -> Dict[str, Any]:
        """Run pylint analysis."""
        try:
            result = subprocess.run(
                ["pylint", temp_file, "--output-format=json", "--score=yes"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.stdout:
                messages = json.loads(result.stdout)
                return {
                    "tool": "pylint",
                    "issues": messages,
                    "count": len(messages)
                }
        except subprocess.TimeoutExpired:
            return {"tool": "pylint", "error": "Timeout"}
        except FileNotFoundError:
            return {"tool": "pylint", "error": "Not installed"}
        except Exception as e:
            return {"tool": "pylint", "error": str(e)}
        return {"tool": "pylint", "issues": [], "count": 0}
    
    @staticmethod
    async def run_flake8(code: str, temp_file: str) -> Dict[str, Any]:
        """Run flake8 analysis."""
        try:
            result = subprocess.run(
                ["flake8", temp_file, "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # flake8 doesn't have built-in JSON format, parse output
            issues = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Format: filename:line:col: error_code message
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        issues.append({
                            "line": parts[1],
                            "column": parts[2],
                            "message": parts[3].strip()
                        })
            return {
                "tool": "flake8",
                "issues": issues,
                "count": len(issues)
            }
        except subprocess.TimeoutExpired:
            return {"tool": "flake8", "error": "Timeout"}
        except FileNotFoundError:
            return {"tool": "flake8", "error": "Not installed"}
        except Exception as e:
            return {"tool": "flake8", "error": str(e)}
    
    @staticmethod
    async def run_mypy(code: str, temp_file: str) -> Dict[str, Any]:
        """Run mypy type checking."""
        try:
            result = subprocess.run(
                ["mypy", temp_file, "--show-column-numbers", "--no-error-summary"],
                capture_output=True,
                text=True,
                timeout=30
            )
            issues = []
            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    issues.append({"message": line.strip()})
            return {
                "tool": "mypy",
                "issues": issues,
                "count": len(issues)
            }
        except subprocess.TimeoutExpired:
            return {"tool": "mypy", "error": "Timeout"}
        except FileNotFoundError:
            return {"tool": "mypy", "error": "Not installed"}
        except Exception as e:
            return {"tool": "mypy", "error": str(e)}
    
    @staticmethod
    async def run_bandit(code: str, temp_file: str) -> Dict[str, Any]:
        """Run bandit security analysis."""
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    "tool": "bandit",
                    "issues": data.get("results", []),
                    "count": len(data.get("results", [])),
                    "metrics": data.get("metrics", {})
                }
        except subprocess.TimeoutExpired:
            return {"tool": "bandit", "error": "Timeout"}
        except FileNotFoundError:
            return {"tool": "bandit", "error": "Not installed"}
        except Exception as e:
            return {"tool": "bandit", "error": str(e)}
        return {"tool": "bandit", "issues": [], "count": 0}
    
    @staticmethod
    async def run_radon(code: str, temp_file: str) -> Dict[str, Any]:
        """Run radon complexity analysis."""
        try:
            # Cyclomatic complexity
            cc_result = subprocess.run(
                ["radon", "cc", temp_file, "-s", "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Maintainability index
            mi_result = subprocess.run(
                ["radon", "mi", temp_file, "-s", "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            complexity = json.loads(cc_result.stdout) if cc_result.stdout else {}
            maintainability = json.loads(mi_result.stdout) if mi_result.stdout else {}
            
            return {
                "tool": "radon",
                "complexity": complexity,
                "maintainability": maintainability
            }
        except subprocess.TimeoutExpired:
            return {"tool": "radon", "error": "Timeout"}
        except FileNotFoundError:
            return {"tool": "radon", "error": "Not installed"}
        except Exception as e:
            return {"tool": "radon", "error": str(e)}
    
    @staticmethod
    async def analyze_ast(code: str) -> Dict[str, Any]:
        """Custom AST analysis for additional insights."""
        issues = []
        stats = {
            "functions": 0,
            "classes": 0,
            "lines": len(code.splitlines()),
            "imports": 0
        }
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "tool": "ast",
                "error": f"Syntax error: {e}",
                "stats": stats
            }
        
        class CodeVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                stats["functions"] += 1
                # Check for missing docstring
                if not ast.get_docstring(node):
                    issues.append({
                        "type": "missing_docstring",
                        "line": node.lineno,
                        "severity": "info",
                        "message": f"Function '{node.name}' missing docstring"
                    })
                # Check for too many arguments
                if len(node.args.args) > 7:
                    issues.append({
                        "type": "too_many_args",
                        "line": node.lineno,
                        "severity": "warning",
                        "message": f"Function '{node.name}' has {len(node.args.args)} parameters (>7)"
                    })
                # Check function length
                func_lines = (node.end_lineno or node.lineno) - node.lineno
                if func_lines > 50:
                    issues.append({
                        "type": "long_function",
                        "line": node.lineno,
                        "severity": "warning",
                        "message": f"Function '{node.name}' is {func_lines} lines long (>50)"
                    })
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                stats["classes"] += 1
                if not ast.get_docstring(node):
                    issues.append({
                        "type": "missing_docstring",
                        "line": node.lineno,
                        "severity": "info",
                        "message": f"Class '{node.name}' missing docstring"
                    })
                self.generic_visit(node)
            
            def visit_Import(self, node):
                stats["imports"] += len(node.names)
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                stats["imports"] += len(node.names)
                # Check for wildcard imports
                for alias in node.names:
                    if alias.name == '*':
                        issues.append({
                            "type": "wildcard_import",
                            "line": node.lineno,
                            "severity": "warning",
                            "message": f"Wildcard import from {node.module}"
                        })
                self.generic_visit(node)
        
        CodeVisitor().visit(tree)
        
        return {
            "tool": "ast",
            "issues": issues,
            "stats": stats,
            "count": len(issues)
        }


######################### Test Generation #########################


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


######################### MCP Tool Handlers #########################


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="code_review",
            description="Comprehensive code review using multiple static analysis tools (pylint, flake8, mypy, bandit, radon). Returns detailed issues, security vulnerabilities, complexity metrics, and improvement suggestions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code to analyze"
                    },
                    "analyzers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of analyzers to use (pylint, flake8, mypy, bandit, radon, ast). Default: all",
                        "default": ["pylint", "flake8", "mypy", "bandit", "radon", "ast"]
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="generate_tests",
            description="Generate intelligent pytest unit tests from Python source code using AST analysis. Creates multiple test cases including happy path, edge cases, exception handling, and type validation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code to generate tests for"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "Module name for imports in tests (default: 'module')",
                        "default": "module"
                    },
                    "save": {
                        "type": "boolean",
                        "description": "Whether to save the generated tests to a file (default: false)",
                        "default": False
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="run_tests",
            description="Execute pytest tests with coverage reporting. Runs tests in an isolated environment and returns detailed results including pass/fail status, coverage percentage, and execution time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_code": {
                        "type": "string",
                        "description": "Pytest test code to execute"
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Source code being tested (for coverage analysis)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["test_code"]
            }
        ),
        Tool(
            name="format_code",
            description="Auto-format Python code using black and autopep8. Returns formatted, PEP8-compliant code with consistent style.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code to format"
                    },
                    "line_length": {
                        "type": "integer",
                        "description": "Maximum line length (default: 88 for black)",
                        "default": 88
                    }
                },
                "required": ["code"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle MCP tool calls."""
    
    if name == "code_review":
        code = arguments.get("code", "")
        analyzers = arguments.get("analyzers", ["pylint", "flake8", "mypy", "bandit", "radon", "ast"])
        
        if not code:
            return [TextContent(type="text", text="Error: No code provided")]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            results = {
                "summary": {
                    "total_issues": 0,
                    "critical": 0,
                    "warning": 0,
                    "info": 0
                },
                "analyzers": {}
            }
            
            # Run selected analyzers
            if "pylint" in analyzers:
                results["analyzers"]["pylint"] = await CodeAnalyzer.run_pylint(code, temp_file)
                results["summary"]["total_issues"] += results["analyzers"]["pylint"].get("count", 0)
            
            if "flake8" in analyzers:
                results["analyzers"]["flake8"] = await CodeAnalyzer.run_flake8(code, temp_file)
                results["summary"]["total_issues"] += results["analyzers"]["flake8"].get("count", 0)
            
            if "mypy" in analyzers:
                results["analyzers"]["mypy"] = await CodeAnalyzer.run_mypy(code, temp_file)
                results["summary"]["total_issues"] += results["analyzers"]["mypy"].get("count", 0)
            
            if "bandit" in analyzers:
                results["analyzers"]["bandit"] = await CodeAnalyzer.run_bandit(code, temp_file)
                security_count = results["analyzers"]["bandit"].get("count", 0)
                results["summary"]["total_issues"] += security_count
                results["summary"]["critical"] += security_count
            
            if "radon" in analyzers:
                results["analyzers"]["radon"] = await CodeAnalyzer.run_radon(code, temp_file)
            
            if "ast" in analyzers:
                results["analyzers"]["ast"] = await CodeAnalyzer.analyze_ast(code)
                results["summary"]["total_issues"] += results["analyzers"]["ast"].get("count", 0)
            
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        finally:
            os.unlink(temp_file)
    
    elif name == "generate_tests":
        code = arguments.get("code", "")
        module_name = arguments.get("module_name", "module")
        save = arguments.get("save", False)
        
        if not code:
            return [TextContent(type="text", text="Error: No code provided")]
        
        test_code = TestGenerator.generate_tests(code, module_name)
        
        result = {
            "test_code": test_code,
            "lines": len(test_code.splitlines()),
            "saved": False
        }
        
        if save:
            with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
                f.write(test_code)
                result["saved"] = True
                result["file_path"] = f.name
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "run_tests":
        test_code = arguments.get("test_code", "")
        source_code = arguments.get("source_code", "")
        timeout = arguments.get("timeout", 30)
        
        if not test_code:
            return [TextContent(type="text", text="Error: No test code provided")]
        
        # Create temporary directory for test execution
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write source code if provided
            if source_code:
                module_path = os.path.join(tmpdir, "module.py")
                with open(module_path, 'w') as f:
                    f.write(source_code)
            
            # Write test code
            test_path = os.path.join(tmpdir, "test_module.py")
            with open(test_path, 'w') as f:
                f.write(test_code)
            
            # Run pytest with coverage
            try:
                cmd = [
                    sys.executable, "-m", "pytest",
                    test_path,
                    "-v",
                    "--tb=short",
                    f"--timeout={timeout}"
                ]
                
                if source_code:
                    cmd.extend(["--cov=module", "--cov-report=json"])
                
                result = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout + 5
                )
                
                output = {
                    "status": "passed" if result.returncode == 0 else "failed",
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "coverage": None
                }
                
                # Read coverage if available
                cov_file = os.path.join(tmpdir, "coverage.json")
                if os.path.exists(cov_file):
                    with open(cov_file) as f:
                        cov_data = json.load(f)
                        output["coverage"] = {
                            "percent": cov_data.get("totals", {}).get("percent_covered"),
                            "lines_covered": cov_data.get("totals", {}).get("covered_lines"),
                            "lines_total": cov_data.get("totals", {}).get("num_statements")
                        }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(output, indent=2)
                )]
            except subprocess.TimeoutExpired:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Test execution timeout"}, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    elif name == "format_code":
        code = arguments.get("code", "")
        line_length = arguments.get("line_length", 88)
        
        if not code:
            return [TextContent(type="text", text="Error: No code provided")]
        
        formatted = code
        errors = []
        
        # Try black first
        try:
            import black
            mode = black.Mode(line_length=line_length)
            formatted = black.format_str(code, mode=mode)
        except ImportError:
            errors.append("black not installed, trying autopep8")
            try:
                import autopep8
                formatted = autopep8.fix_code(code, options={'max_line_length': line_length})
            except ImportError:
                errors.append("autopep8 not installed, returning original code")
        except Exception as e:
            errors.append(f"Formatting error: {str(e)}")
        
        result = {
            "formatted_code": formatted,
            "changes": formatted != code,
            "errors": errors if errors else None
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


######################### Main Entry Point #########################


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
