#!/usr/bin/env python3
"""
Example usage of NeuroDev MCP Server tools
"""

import json
import asyncio
from neurodev_mcp import CodeAnalyzer, TestGenerator, TestExecutor


async def example_code_review():
    """Example: Code review analysis"""
    print("=" * 60)
    print("EXAMPLE 1: Code Review")
    print("=" * 60)
    
    sample_code = '''
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)

def process_data(data, flag, option, mode, setting, config, params):
    # Function with too many parameters
    if flag:
        return data * 2
    return data
'''
    
    print("\nAnalyzing code...\n")
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_code)
        temp_file = f.name
    
    try:
        # Run AST analysis
        result = await CodeAnalyzer.analyze_ast(sample_code)
        print("AST Analysis Results:")
        print(json.dumps(result, indent=2))
    finally:
        import os
        os.unlink(temp_file)


def example_test_generation():
    """Example: Generate tests for code"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Test Generation")
    print("=" * 60)
    
    sample_code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    """A simple calculator."""
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
'''
    
    print("\nGenerating tests...\n")
    
    tests = TestGenerator.generate_tests(sample_code, "calculator")
    print("Generated Test Code:")
    print("-" * 60)
    print(tests)


def example_formats():
    """Example: Code formatting"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Code Formatting")
    print("=" * 60)
    
    messy_code = '''
def   messy_function(  x,y,   z  ):
        result=x+y+z
        if result>10:
                    return   True
        else:
             return False
'''
    
    print("\nOriginal Code:")
    print(messy_code)
    
    try:
        import black
        mode = black.Mode(line_length=88)
        formatted = black.format_str(messy_code, mode=mode)
        print("\nFormatted Code:")
        print(formatted)
    except ImportError:
        print("\nNote: Install 'black' for formatting: pip install black")


if __name__ == "__main__":
    print("NeuroDev MCP Server - Usage Examples")
    print()
    
    # Run examples
    asyncio.run(example_code_review())
    example_test_generation()
    example_formats()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
