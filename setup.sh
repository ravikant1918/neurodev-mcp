#!/bin/bash

# NeuroDev MCP Server Setup Script

echo "🚀 Setting up NeuroDev MCP Server..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -e .

echo "✅ Setup complete!"
echo ""
echo "To use the server:"
echo "1. Update claude_desktop_config.json:"
echo '   "command": "python", "args": ["-m", "neurodev_mcp.server"]'
echo "2. Copy config to ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "3. Restart Claude Desktop"
echo ""
echo "To test locally:"
echo "  python -m neurodev_mcp.server"
