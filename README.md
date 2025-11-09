<div align="center">

# 🧠 NeuroDev MCP Server

### *Intelligent Code Analysis, Test Generation & Execution*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-success.svg)](./test_installation.py)

**A powerful Model Context Protocol (MCP) server that supercharges your Python development workflow with AI-powered code review, intelligent test generation, and comprehensive test execution.**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Tools](#-available-tools) • [Examples](#-usage-examples)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔍 **Code Review**
- **6 Powerful Analyzers**
  - `pylint` - Code quality & PEP8
  - `flake8` - Style enforcement
  - `mypy` - Type checking
  - `bandit` - Security scanning
  - `radon` - Complexity metrics
  - `AST` - Custom inspections
- Real-time issue detection
- Security vulnerability scanning
- Complexity & maintainability scores

</td>
<td width="50%">

### 🧪 **Test Generation**
- **Intelligent AST Analysis**
  - Auto-generate pytest tests
  - Happy path coverage
  - Edge case handling
  - Exception testing
  - Type validation tests
- Supports functions & classes
- Type-hint aware

</td>
</tr>
<tr>
<td width="50%">

### ▶️ **Test Execution**
- **Comprehensive Testing**
  - Isolated environment
  - Coverage reporting
  - Line-by-line analysis
  - Timeout protection
- Detailed pass/fail results
- Performance metrics

</td>
<td width="50%">

### 🎨 **Code Formatting**
- **Auto-formatting**
  - `black` - Opinionated style
  - `autopep8` - PEP8 compliance
- Configurable line length
- Consistent code style
- One-command formatting

</td>
</tr>
</table>

---

## 📦 Installation

### **Quick Install**

\`\`\`bash
```bash
# Clone the repository
git clone https://github.com/ravikant1918/neurodev-mcp.git
cd neurodev-mcp

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# Install the package
pip install -e .
\`\`\`

### **Verify Installation**

\`\`\`bash
# Run tests (should show 15/15 passing)
python test_installation.py

# Test the server
python -m neurodev_mcp.server
\`\`\`

<details>
<summary><b>📁 Project Structure</b> (click to expand)</summary>

\`\`\`
neurodev-mcp/
├─ neurodev_mcp/              # 📦 Main package
│   ├─ __init__.py            # Package exports
│   ├─ server.py              # MCP server entry point
│   ├─ analyzers/             # 🔍 Code analysis
│   │   ├─ __init__.py
│   │   └─ code_analyzer.py   # Multi-tool static analysis
│   ├─ generators/            # 🧪 Test generation
│   │   ├─ __init__.py
│   │   └─ test_generator.py  # AST-based test creation
│   └─ executors/             # ▶️ Test execution
│       ├─ __init__.py
│       └─ test_executor.py   # Test running & formatting
├─ pyproject.toml             # Project configuration
├─ README.md                  # This file
├─ test_installation.py       # Installation validator
├─ examples.py                # Usage examples
└─ requirements.txt           # Dependencies
```

</details>

---

## 🚀 Quick Start

### **Step 1: Configure Your MCP Client**

<details open>
<summary><b>🖥️ Claude Desktop</b></summary>

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "neurodev-mcp": {
      "command": "/absolute/path/to/neurodev-mcp/.venv/bin/python",
      "args": ["-m", "neurodev_mcp.server"]
    }
  }
}
```

> 💡 **Tip:** Replace `/absolute/path/to/neurodev-mcp` with your actual path

</details>

<details>
<summary><b>🔧 Cline (VSCode)</b></summary>

Add to your MCP settings:

```json
{
  "neurodev-mcp": {
    "command": "python",
    "args": ["-m", "neurodev_mcp.server"]
  }
}
```

</details>

<details>
<summary><b>🐍 Standalone Usage</b></summary>

Run the server directly:

```bash
# Using the module
python -m neurodev_mcp.server

# Or as a command (if installed)
neurodev-mcp
```

</details>

### **Step 2: Restart Your Client**

Restart Claude Desktop or reload VSCode to load the server.

### **Step 3: Start Using! 🎉**

Try these commands with your AI assistant:
- *"Review this Python code for issues"*
- *"Generate unit tests for this function"*
- *"Run these tests with coverage"*
- *"Format this code to PEP8 standards"*

---

## 🌐 Transport Options

NeuroDev MCP supports multiple transport protocols for different use cases:

### **STDIO (Default) - Local CLI**

Perfect for local development with MCP clients like Claude Desktop or Cline:

```bash
# Default STDIO transport
neurodev-mcp

# Or explicitly specify STDIO
neurodev-mcp --transport stdio
```

**Configuration (Claude Desktop):**
```json
{
  "mcpServers": {
    "neurodev-mcp": {
      "command": "neurodev-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

### **SSE (Server-Sent Events) - Web Integration**

For web-based integrations and HTTP streaming:

```bash
# Run with SSE on default port (8000)
neurodev-mcp --transport sse

# Custom host and port
neurodev-mcp --transport sse --host 0.0.0.0 --port 3000
```

**Endpoints:**
- **SSE Stream:** `http://localhost:8000/sse`
- **Messages:** `http://localhost:8000/messages` (POST)

**Web Client Example:**
```javascript
const sse = new EventSource('http://localhost:8000/sse');

sse.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send message
fetch('http://localhost:8000/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    method: 'tools/call',
    params: {
      name: 'code_review',
      arguments: { code: 'def test(): pass', analyzers: ['pylint'] }
    }
  })
});
```

### **Transport Comparison**

| Transport | Use Case | Best For |
|-----------|----------|----------|
| **STDIO** | Local CLI clients | Claude Desktop, Cline, local development |
| **SSE** | Web integrations | Browser apps, webhooks, remote clients |

---

## 🛠️ Available Tools

### **1. `code_review`**
🔍 Comprehensive code analysis with multiple static analysis tools

**Input:**
```json
{
  "code": "def calculate(x):\n    return x * 2",
  "analyzers": ["pylint", "flake8", "mypy", "bandit", "radon", "ast"]
}
```

**Output:**
- Detailed issue reports from each analyzer
- Security vulnerabilities
- Complexity metrics
- Code quality scores
- Line-by-line suggestions

---

### **2. `generate_tests`**
🧪 Intelligent pytest test generation using AST analysis

**Input:**
```json
{
  "code": "def add(a: int, b: int) -> int:\n    return a + b",
  "module_name": "calculator",
  "save": false
}
```

**Output:**
- Complete pytest test suite
- Multiple test cases (happy path, edge cases, exceptions)
- Type validation tests
- Ready-to-run test code

---

### **3. `run_tests`**
▶️ Execute pytest tests with coverage reporting

**Input:**
```json
{
  "test_code": "def test_add():\n    assert add(1, 2) == 3",
  "source_code": "def add(a, b):\n    return a + b",
  "timeout": 30
}
```

**Output:**
- Pass/fail status
- Coverage percentage
- Line coverage details
- Execution time
- Detailed stdout/stderr

---

### **4. `format_code`**
🎨 Auto-format Python code to PEP8 standards

**Input:**
```json
{
  "code": "def   messy(  x,y  ):\n        return x+y",
  "line_length": 88
}
```

**Output:**
- Beautifully formatted code
- PEP8 compliant
- Consistent style
- Change detection

---

## 💡 Usage Examples

### **Example 1: Complete Code Review Workflow**

```
You: "Review this code for issues and security problems"

[paste code]

AI: [Uses code_review tool]
    → Finds 3 style issues
    → Detects 1 security vulnerability
    → Suggests complexity improvements
    
You: "Fix those issues and show me the updated code"

AI: [Provides fixed code with explanations]
```

### **Example 2: Test Generation & Execution**

```
You: "Generate tests for this function and run them"

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

AI: [Uses generate_tests tool]
    → Creates 5 test cases
    → Includes edge cases (zero, negative numbers)
    → Tests exception handling
    
    [Uses run_tests tool]
    → 5/5 tests passing ✓
    → 100% code coverage
    → All edge cases handled
```

### **Example 3: Code Formatting**

```
You: "Format this messy code"

def   calculate(  x,y,z  ):
        result=x+y+z
        if result>10:
                    return   True
        return False

AI: [Uses format_code tool]
    → Applies black formatting
    → Returns clean, PEP8-compliant code

def calculate(x, y, z):
    result = x + y + z
    if result > 10:
        return True
    return False
```

---

## 📋 Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | ≥0.9.0 | Model Context Protocol SDK |
| `pylint` | ≥3.0.0 | Code quality analysis |
| `flake8` | ≥7.0.0 | Style checking |
| `mypy` | ≥1.7.0 | Static type checking |
| `bandit` | ≥1.7.5 | Security scanning |
| `radon` | ≥6.0.1 | Complexity metrics |
| `black` | ≥23.12.0 | Code formatting |
| `autopep8` | ≥2.0.4 | PEP8 formatting |
| `pytest` | ≥7.4.3 | Testing framework |
| `pytest-cov` | ≥4.1.0 | Coverage reporting |
| `pytest-timeout` | ≥2.2.0 | Test timeouts |

**Python:** 3.8 or higher

---

## 🧪 Development

### **Running Tests**

```bash
# Run installation tests
python test_installation.py

# Run examples
python examples.py

# Run pytest (if you add tests)
pytest
```

### **Using as a Library**

```python
from neurodev_mcp import CodeAnalyzer, TestGenerator, TestExecutor
import asyncio

# Analyze code
code = "def hello(): print('world')"
result = asyncio.run(CodeAnalyzer.analyze_ast(code))

# Generate tests
tests = TestGenerator.generate_tests(code, "mymodule")

# Run tests
output = TestExecutor.run_tests(test_code, source_code)
```

---

## ❓ Troubleshooting

<details>
<summary><b>Server not appearing in MCP client?</b></summary>

- ✅ Check that the path in config is **absolute**
- ✅ Ensure the Python executable path is correct
- ✅ Restart Claude Desktop or VSCode **completely**
- ✅ Check server logs for errors

</details>

<details>
<summary><b>Import or module errors?</b></summary>

```bash
# Reinstall the package
pip install -e .

# Verify installation
python -c "from neurodev_mcp import CodeAnalyzer; print('✓ OK')"

# Run installation tests
python test_installation.py
```

</details>

<details>
<summary><b>Tests failing?</b></summary>

- ✅ Ensure Python 3.8+ is installed
- ✅ Activate virtual environment: `source .venv/bin/activate`
- ✅ Reinstall dependencies: `pip install -e .`
- ✅ Run: `python test_installation.py` to diagnose

</details>

<details>
<summary><b>Performance issues?</b></summary>

- Some analyzers (pylint, mypy) can be slow on large files
- Use specific analyzers: `"analyzers": ["flake8", "ast"]`
- Increase timeout for large test suites
- Consider caching results (future feature)

</details>

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python test_installation.py`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### **Future Enhancements**
- [ ] Additional analyzers (pydocstyle, vulture)
- [ ] Result caching for performance
- [ ] Configuration file support
- [ ] Web dashboard
- [ ] Multi-language support
- [ ] CI/CD pipeline

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Powered by [pylint](https://pylint.org/), [flake8](https://flake8.pycqa.org/), [mypy](http://mypy-lang.org/), [bandit](https://bandit.readthedocs.io/), [radon](https://radon.readthedocs.io/)
- Testing with [pytest](https://pytest.org/)
- Formatting with [black](https://black.readthedocs.io/)

---

## 📞 Support

- 📖 **Documentation**: You're reading it!
- 🐛 **Issues**: [GitHub Issues](https://github.com/ravikant1918/neurodev-mcp/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/ravikant1918/neurodev-mcp/discussions)
- 📧 **Email**: team@neurodev.io

---

<div align="center">

### **Ready to supercharge your Python development!** 🚀

Made with ❤️ by the NeuroDev Team

[⭐ Star on GitHub](https://github.com/ravikant1918/neurodev-mcp) • [🐛 Report Bug](https://github.com/ravikant1918/neurodev-mcp/issues) • [✨ Request Feature](https://github.com/ravikant1918/neurodev-mcp/issues)

</div>
