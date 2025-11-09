"""Test execution module with coverage reporting."""

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict


class TestExecutor:
    """Execute pytest tests with coverage reporting."""
    
    @staticmethod
    def run_tests(
        test_code: str,
        source_code: str = "",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute pytest tests in an isolated environment.
        
        Args:
            test_code: Pytest test code to execute
            source_code: Source code being tested (for coverage)
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with test results and coverage data
        """
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
                
                return output
            except subprocess.TimeoutExpired:
                return {"error": "Test execution timeout"}
            except Exception as e:
                return {"error": str(e)}
    
    @staticmethod
    def format_code(code: str, line_length: int = 88) -> Dict[str, Any]:
        """
        Format Python code using black and autopep8.
        
        Args:
            code: Python source code to format
            line_length: Maximum line length
            
        Returns:
            Dictionary with formatted code and any errors
        """
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
        
        return {
            "formatted_code": formatted,
            "changes": formatted != code,
            "errors": errors if errors else None
        }
