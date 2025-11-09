#!/usr/bin/env python3
"""
Test script to verify NeuroDev MCP Server installation and functionality
"""

import sys
import subprocess


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠️  Warning: Python 3.8+ recommended")
        return False
    return True


def check_package(package_name):
    """Check if a package is installed"""
    try:
        __import__(package_name.replace('-', '_'))
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} - NOT INSTALLED")
        return False


def test_mcp_server():
    """Test MCP server import"""
    try:
        from neurodev_mcp import CodeAnalyzer, TestGenerator, TestExecutor
        print("✓ MCP Server modules import successfully")
        return True
    except Exception as e:
        print(f"✗ MCP Server import failed: {e}")
        return False


def test_code_analyzer():
    """Test CodeAnalyzer functionality"""
    try:
        from neurodev_mcp import CodeAnalyzer
        import tempfile
        import os
        import asyncio
        
        test_code = "def hello():\n    print('world')\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        try:
            result = asyncio.run(CodeAnalyzer.analyze_ast(test_code))
            if result and 'tool' in result and result['tool'] == 'ast':
                print("✓ CodeAnalyzer working correctly")
                return True
            else:
                print("✗ CodeAnalyzer returned unexpected result")
                return False
        finally:
            os.unlink(temp_file)
    except Exception as e:
        print(f"✗ CodeAnalyzer test failed: {e}")
        return False


def test_test_generator():
    """Test TestGenerator functionality"""
    try:
        from neurodev_mcp import TestGenerator
        
        test_code = "def add(a, b):\n    return a + b\n"
        result = TestGenerator.generate_tests(test_code, "test_module")
        
        if result and "test_add_basic" in result:
            print("✓ TestGenerator working correctly")
            return True
        else:
            print("✗ TestGenerator returned unexpected result")
            return False
    except Exception as e:
        print(f"✗ TestGenerator test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("NeuroDev MCP Server - Installation Test")
    print("=" * 60)
    print()
    
    results = []
    
    print("Checking Python version...")
    results.append(check_python_version())
    print()
    
    print("Checking required packages...")
    packages = [
        "mcp",
        "pylint",
        "flake8",
        "mypy",
        "bandit",
        "radon",
        "autopep8",
        "black",
        "pytest",
        "pytest-cov",
        "pydantic"
    ]
    for package in packages:
        results.append(check_package(package))
    print()
    
    print("Testing MCP server components...")
    results.append(test_mcp_server())
    results.append(test_code_analyzer())
    results.append(test_test_generator())
    print()
    
    print("=" * 60)
    success_rate = sum(results) / len(results) * 100
    print(f"Test Results: {sum(results)}/{len(results)} passed ({success_rate:.1f}%)")
    print("=" * 60)
    
    if all(results):
        print("\n🎉 All tests passed! MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Configure your MCP client (Claude Desktop, Cline, etc.)")
        print("2. Add this server to your MCP configuration")
        print("3. Start using the tools!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nTry running: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
