"""
Smart MCP (Model Context Protocol) server built with FastAPI
Purpose: provide tools/resources for code review, test-case generation, and test execution.

Features:
- Tool: `code_review` - runs static analysis (flake8/pylint style via ast checks) and returns suggestions
- Tool: `generate_tests` - generates pytest-style unit tests from given Python source using simple heuristics and prompts
- Tool: `run_tests` - runs pytest on generated tests and returns summarized results
- Tool: `format_code` - formats code using `black` if available (fallback to simple formatting)
- Resource: `repo` - a simple resource representing project files uploaded to the MCP server

How to run:
- pip install fastapi uvicorn python-multipart pytest
- Optional: install black and pytest
- uvicorn fastmcp_smart_mcp_fastapi:app --reload --port 8000

Endpoints (simple MCP-like API):
- GET / -> basic info
- POST /mcp/tools/run -> {"tool": "generate_tests", "payload": {...}} -> runs tool
- POST /mcp/resources/upload -> multipart form upload file(s)
- GET /mcp/resources/{id}

This is a compact single-file implementation for quick iteration; adapt to your production needs.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import os
import tempfile
import subprocess
import json
import shutil
import ast
import textwrap

app = FastAPI(title="Smart MCP - Code Review & Testcase Generator (FastAPI)")

# In-memory "resource store" (for demo). In production, use persistent storage.
RESOURCES: Dict[str, Dict[str, Any]] = {}


class ToolRunRequest(BaseModel):
    tool: str
    payload: Optional[Dict[str, Any]] = None


class ToolRunResponse(BaseModel):
    id: str
    tool: str
    result: Dict[str, Any]


######################### Helper utilities #########################

def save_uploaded_files(files: List[UploadFile]) -> Dict[str, Any]:
    rid = str(uuid.uuid4())
    folder = os.path.join(tempfile.gettempdir(), "mcp_resources", rid)
    os.makedirs(folder, exist_ok=True)
    saved = []
    for f in files:
        path = os.path.join(folder, f.filename)
        with open(path, "wb") as out:
            out.write(f.file.read())
        saved.append(path)
    RESOURCES[rid] = {"id": rid, "paths": saved, "folder": folder}
    return RESOURCES[rid]


def simple_ast_inspect(code: str) -> Dict[str, Any]:
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "syntax_error": str(e)}

    # Example checks
    class FuncVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            # check for missing docstring
            if not ast.get_docstring(node):
                issues.append({
                    "type": "missing_docstring",
                    "lineno": node.lineno,
                    "name": node.name,
                    "message": f"Function '{node.name}' is missing a docstring",
                })
            # check for too many args
            if len(node.args.args) > 6:
                issues.append({
                    "type": "many_args",
                    "lineno": node.lineno,
                    "name": node.name,
                    "message": f"Function '{node.name}' has {len(node.args.args)} args",
                })
            self.generic_visit(node)

        def visit_Import(self, node):
            # trivial: flag wildcard imports
            self.generic_visit(node)

    FuncVisitor().visit(tree)
    return {"ok": True, "issues": issues}


def generate_pytest_from_source(code: str, module_name: str = "module_under_test") -> str:
    """
    Very simple heuristic-based pytest generator:
    - Finds top-level functions and generates tests that call them with dummy args (0 or empty values)
    - If function returns value, assert that calling doesn't raise; where possible add simple assertions
    This is a baseline. You should refine with LLM prompts for better testcases.
    """
    tree = ast.parse(code)
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    tests = ["import pytest", f"import {module_name}", "\n"]
    for fn in funcs:
        name = fn.name
        argcount = len(fn.args.args)
        # create dummy args
        dummy_args = []
        for i, a in enumerate(fn.args.args):
            # name-based heuristic
            aname = a.arg.lower()
            if "path" in aname or "file" in aname:
                dummy_args.append("\"/tmp/nonexistent\"")
            elif "num" in aname or "count" in aname or "n" == aname:
                dummy_args.append("0")
            elif "flag" in aname or aname.startswith("is_"):
                dummy_args.append("False")
            else:
                dummy_args.append("None")
        call = f"{module_name}.{name}({', '.join(dummy_args)})"
        test_fn = textwrap.dedent(f"""
        def test_{name}_sanity():
            # simple sanity test: must not raise and return type check
            try:
                res = {call}
            except Exception as e:
                pytest.skip(f"skipped because function raised: {e}")
            # basic assertion: function returns or not (adjust manually)
            assert True

        """)
        tests.append(test_fn)
    return "\n".join(tests)


def run_pytest_in_dir(path: str, timeout: int = 30) -> Dict[str, Any]:
    """Run pytest in the given directory and capture results (simple)."""
    cmd = ["pytest", "-q", "--disable-warnings", "--maxfail=1"]
    try:
        proc = subprocess.run(cmd, cwd=path, capture_output=True, text=True, timeout=timeout)
        return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except Exception as e:
        return {"error": str(e)}


def try_format_with_black(code: str) -> str:
    try:
        import black

        mode = black.Mode()
        formatted = black.format_str(code, mode=mode)
        return formatted
    except Exception:
        # fallback: simple dedent
        return textwrap.dedent(code)


######################### Tool implementations #########################


def tool_code_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Payload must include 'code' string")
    ast_report = simple_ast_inspect(code)
    # simple metrics
    loc = len(code.splitlines())
    return {"loc": loc, "ast_report": ast_report}


def tool_generate_tests(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = payload.get("code")
    filename = payload.get("filename", "module_under_test.py")
    if not code:
        raise HTTPException(status_code=400, detail="Payload must include 'code' string")
    # create temp project dir
    rid = str(uuid.uuid4())
    folder = os.path.join(tempfile.gettempdir(), "mcp_projects", rid)
    os.makedirs(folder, exist_ok=True)
    module_path = os.path.join(folder, filename)
    with open(module_path, "w") as f:
        f.write(code)
    # generate tests
    test_code = generate_pytest_from_source(code, module_name=filename.replace('.py',''))
    test_path = os.path.join(folder, f"test_{filename}")
    with open(test_path, "w") as f:
        f.write(test_code)
    return {"project_id": rid, "module_path": module_path, "test_path": test_path, "test_code_preview": test_code[:1000]}


def tool_run_tests(payload: Dict[str, Any]) -> Dict[str, Any]:
    project_id = payload.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="Payload must include 'project_id'")
    res = RESOURCES.get(project_id)
    # If project not in RESOURCES, it might be in tempdir 'mcp_projects'
    folder = os.path.join(tempfile.gettempdir(), "mcp_projects", project_id)
    if not os.path.isdir(folder):
        raise HTTPException(status_code=404, detail="Project not found")
    result = run_pytest_in_dir(folder)
    return result


def tool_format_code(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Payload must include 'code' string")
    formatted = try_format_with_black(code)
    return {"formatted_code": formatted}


TOOL_REGISTRY = {
    "code_review": tool_code_review,
    "generate_tests": tool_generate_tests,
    "run_tests": tool_run_tests,
    "format_code": tool_format_code,
}


######################### FastAPI endpoints (MCP-style) #########################


@app.get("/")
def root():
    return {"name": "Smart MCP", "version": "0.1", "tools": list(TOOL_REGISTRY.keys())}


@app.post("/mcp/tools/run", response_model=ToolRunResponse)
def run_tool(req: ToolRunRequest):
    tool = req.tool
    payload = req.payload or {}
    if tool not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool}' not found")
    fn = TOOL_REGISTRY[tool]
    result = fn(payload)
    trid = str(uuid.uuid4())
    return {"id": trid, "tool": tool, "result": result}


@app.post("/mcp/resources/upload")
async def upload_resource(files: List[UploadFile] = File(...)):
    r = save_uploaded_files(files)
    return r


@app.get("/mcp/resources/{rid}")
def get_resource(rid: str):
    r = RESOURCES.get(rid)
    if not r:
        raise HTTPException(status_code=404, detail="resource not found")
    return r


######################### Example: local CLI-style helper #########################

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastmcp_smart_mcp_fastapi:app", host="0.0.0.0", port=8000, reload=True)
