"""Code analysis module using multiple static analysis tools."""

import ast
import json
import subprocess
from typing import Any, Dict


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
