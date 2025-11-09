#!/usr/bin/env python3
"""
NeuroDev MCP Server - Main entry point
Built with the official Model Context Protocol SDK

This MCP server provides powerful tools for Python development:
- Code Review: Multi-analyzer static analysis
- Test Generation: Intelligent pytest test generation
- Test Execution: Comprehensive test running with coverage
- Code Formatting: Auto-formatting with black and autopep8

Supports multiple transports:
- STDIO (default): For local CLI usage
- SSE: For web-based integrations
- HTTP: For REST API integrations
"""

import argparse
import asyncio
import json
import os
import sys
import tempfile
from typing import Any, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import SSE transport if available
try:
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    import uvicorn
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

from neurodev_mcp.analyzers import CodeAnalyzer
from neurodev_mcp.generators import TestGenerator
from neurodev_mcp.executors import TestExecutor

# Initialize MCP server
app = Server("neurodev-mcp")


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
        
        output = TestExecutor.run_tests(test_code, source_code, timeout)
        
        return [TextContent(
            type="text",
            text=json.dumps(output, indent=2)
        )]
    
    elif name == "format_code":
        code = arguments.get("code", "")
        line_length = arguments.get("line_length", 88)
        
        if not code:
            return [TextContent(type="text", text="Error: No code provided")]
        
        result = TestExecutor.format_code(code, line_length)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main_stdio():
    """Run the MCP server using STDIO transport (default)."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


async def main_sse(host: str = "0.0.0.0", port: int = 8000):
    """Run the MCP server using SSE transport."""
    if not SSE_AVAILABLE:
        print("Error: SSE transport not available. Install with: pip install mcp[sse]", file=sys.stderr)
        sys.exit(1)
    
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await app.run(
                streams[0],
                streams[1],
                app.create_initialization_options(),
            )
    
    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)
    
    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )
    
    config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    print(f"🚀 NeuroDev MCP Server (SSE) running on http://{host}:{port}")
    print(f"   SSE endpoint: http://{host}:{port}/sse")
    print(f"   Messages endpoint: http://{host}:{port}/messages")
    
    await server.serve()


def main():
    """Main entry point with transport selection."""
    parser = argparse.ArgumentParser(
        description="NeuroDev MCP Server - Code analysis, test generation, and more",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Transport Options:
  stdio (default): Standard input/output for local CLI usage
  sse:             Server-Sent Events for web-based integrations
  
Examples:
  # Run with STDIO (default)
  neurodev-mcp
  
  # Run with SSE on default port (8000)
  neurodev-mcp --transport sse
  
  # Run with SSE on custom host/port
  neurodev-mcp --transport sse --host 0.0.0.0 --port 3000
        """
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (SSE only, default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (SSE only, default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.transport == "stdio":
        asyncio.run(main_stdio())
    elif args.transport == "sse":
        asyncio.run(main_sse(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
